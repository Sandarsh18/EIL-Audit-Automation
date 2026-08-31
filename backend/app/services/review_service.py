from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from app.schemas.review import JobReviewResult, ManualOverride, OverrideRequest, ApprovalRequest
from app.schemas.combined_rules import ManualInputs
from app.services.combined_engine_service import CombinedEngineService
import math

# Memory store: session_id -> { job_number -> { "overrides": Dict, "approved": bool } }
_review_state: Dict[str, Dict[str, Dict[str, Any]]] = {}

class ReviewService:
    @staticmethod
    def _init_session(session_id: str):
        if session_id not in _review_state:
            _review_state[session_id] = {}

    @staticmethod
    def _get_job_state(session_id: str, job_number: str) -> Dict[str, Any]:
        ReviewService._init_session(session_id)
        if job_number not in _review_state[session_id]:
            _review_state[session_id][job_number] = {"overrides": {}, "approved": False}
        return _review_state[session_id][job_number]

    @staticmethod
    def restore_review_state(session_id: str, state: Dict[str, Any]):
        from app.schemas.review import ManualOverride
        
        restored = {}
        for job_num, job_data in state.items():
            job_restored = {"overrides": {}, "approved": job_data.get("approved", False)}
            # Deserialize overrides back to objects
            for field, ovr_dict in job_data.get("overrides", {}).items():
                job_restored["overrides"][field] = ManualOverride(**ovr_dict)
            restored[job_num] = job_restored
            
        _review_state[session_id] = restored

    @staticmethod
    def get_reviews(session_id: str, job_numbers: List[str], evaluation_month: str = None) -> List[JobReviewResult]:
        ReviewService._init_session(session_id)
        
        # 1. Fetch raw combined calculations (WITHOUT overrides, so we get source values)
        raw_combined = {r.job_number: r for r in CombinedEngineService.calculate_combined(session_id, job_numbers, {}, evaluation_month)}
        
        # 2. Build the manual_inputs dict from overrides
        manual_inputs = {}
        for job in job_numbers:
            state = ReviewService._get_job_state(session_id, job)
            ovr = state["overrides"]
            mi = ManualInputs()
            if "ocs_done" in ovr and ovr["ocs_done"].active:
                mi.ocs_done = ovr["ocs_done"].override_value
            if "others" in ovr and ovr["others"].active:
                mi.others = ovr["others"].override_value
            if "expediting" in ovr and ovr["expediting"].active:
                mi.expediting = ovr["expediting"].override_value
            if "meeting" in ovr and ovr["meeting"].active:
                mi.meeting = ovr["meeting"].override_value
            manual_inputs[job] = mi
            
        # 3. Fetch effective combined calculations WITH overrides
        effective_combined = {r.job_number: r for r in CombinedEngineService.calculate_combined(session_id, job_numbers, manual_inputs, evaluation_month)}
        
        results = []
        for job in job_numbers:
            state = ReviewService._get_job_state(session_id, job)
            raw = raw_combined.get(job)
            eff = effective_combined.get(job)
            
            if not eff or not raw:
                continue
                
            # Filter overrides to only include active ones for the effective state in the schema
            # Wait, the schema should return all overrides so the frontend can see the history
            # We'll just return the dictionary as is. The frontend can check `active`.
            
            # Determine Review Status
            status = eff.status
            is_approved = state["approved"]
            
            final_status = "DRAFT"
            if state.get("deleted"):
                final_status = "DELETED"
            elif status == "BLOCKED":
                final_status = "BLOCKED"
                state["approved"] = False # Un-approve if it became blocked
            elif is_approved:
                final_status = "APPROVED"
            elif status == "WARNING":
                final_status = "WARNING"
                
            print(f"REVIEW JOB={job} EVALUATION_MONTH={eff.evidence[0]} INSPECTION_DAYS={eff.inspection} SOURCE=COMBINED_CALCULATION")
            
            results.append(JobReviewResult(
                job_number=job,
                fd=eff.fd,
                running_orders=eff.running_orders,
                ocs_done=eff.ocs_done,
                expediting=eff.expediting,
                native_expediting_used=eff.native_expediting_used,
                inspection=eff.inspection,
                others=eff.others,
                meeting=eff.meeting,
                calculated_total=eff.calculated_total,
                status=final_status,
                warnings=eff.warnings,
                evidence=eff.evidence,
                overrides=state["overrides"]
            ))
            
        return results

    @staticmethod
    def apply_override(session_id: str, job_number: str, request: OverrideRequest) -> JobReviewResult:
        # Validate values
        if request.value is not None:
            if math.isnan(request.value) or math.isinf(request.value):
                raise HTTPException(status_code=400, detail="Value cannot be NaN or Infinity")
            if request.field == "ocs_done" and request.value < 0:
                raise HTTPException(status_code=400, detail="OCS Done cannot be negative.")
                
        # Get source value to store in audit trail
        # Run calculation just for this job without overrides
        raw_res = CombinedEngineService.calculate_combined(session_id, [job_number], {})[0]
        source_val = getattr(raw_res, request.field, None)
        
        state = ReviewService._get_job_state(session_id, job_number)
        state["overrides"][request.field] = ManualOverride(
            field=request.field,
            source_value=source_val,
            override_value=request.value,
            reason=request.reason,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        state["approved"] = False # Any edit resets approval
        
        return ReviewService.get_reviews(session_id, [job_number])[0]

    @staticmethod
    def reset_overrides(session_id: str, job_number: str) -> JobReviewResult:
        state = ReviewService._get_job_state(session_id, job_number)
        for ovr in state["overrides"].values():
            ovr.active = False
        state["approved"] = False
        return ReviewService.get_reviews(session_id, [job_number])[0]


    @staticmethod
    def approve_all(session_id: str, job_numbers: List[str]) -> Dict[str, int]:
        approved_count = 0
        failed_count = 0
        
        # We need to get current states for all requested jobs
        reviews = ReviewService.get_reviews(session_id, job_numbers)
        
        for res in reviews:
            if res.status in ["DRAFT", "WARNING"]:
                # We approve it
                state = ReviewService._get_job_state(session_id, res.job_number)
                state["approved"] = True
                approved_count += 1
            else:
                # BLOCKED or already APPROVED
                failed_count += 1
                
        return {"approved": approved_count, "failed": failed_count}

    @staticmethod
    def approve_job(session_id: str, job_number: str, request: ApprovalRequest) -> JobReviewResult:
        res = ReviewService.get_reviews(session_id, [job_number])[0]
        if res.status == "BLOCKED":
            raise HTTPException(status_code=400, detail="Cannot approve a blocked calculation.")
            
        if res.status == "WARNING" and not request.acknowledge_warnings:
            raise HTTPException(status_code=400, detail="Must explicitly acknowledge warnings to approve.")
            
        state = ReviewService._get_job_state(session_id, job_number)
        state["approved"] = True
        return ReviewService.get_reviews(session_id, [job_number])[0]

    @staticmethod
    def unapprove_job(session_id: str, job_number: str) -> JobReviewResult:
        state = ReviewService._get_job_state(session_id, job_number)
        state["approved"] = False
        return ReviewService.get_reviews(session_id, [job_number])[0]

    @staticmethod
    def delete_job(session_id: str, job_number: str) -> JobReviewResult:
        state = ReviewService._get_job_state(session_id, job_number)
        state["deleted"] = True
        return ReviewService.get_reviews(session_id, [job_number])[0]

    @staticmethod
    def undelete_job(session_id: str, job_number: str) -> JobReviewResult:
        state = ReviewService._get_job_state(session_id, job_number)
        state["deleted"] = False
        return ReviewService.get_reviews(session_id, [job_number])[0]

    @staticmethod
    def delete_all(session_id: str, job_numbers: List[str]) -> Dict[str, int]:
        deleted_count = 0
        failed_count = 0
        
        reviews = ReviewService.get_reviews(session_id, job_numbers)
        
        for res in reviews:
            if res.status in ["DRAFT", "WARNING", "APPROVED"]:
                state = ReviewService._get_job_state(session_id, res.job_number)
                state["deleted"] = True
                deleted_count += 1
            else:
                failed_count += 1
                
        return {"deleted": deleted_count, "failed": failed_count}
