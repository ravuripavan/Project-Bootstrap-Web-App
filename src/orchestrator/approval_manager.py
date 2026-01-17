"""
Approval manager - handles user approval gates.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ApprovalManager:
    """
    Manages user approval gates between workflow phases.
    """

    def __init__(self, db_session=None, websocket_manager=None):
        self.db = db_session
        self.ws_manager = websocket_manager
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}

    async def create_gate(
        self,
        project_id: str,
        phase: str,
        artifact: Dict[str, Any],
    ) -> str:
        """
        Create an approval gate for user review.

        Returns:
            Approval gate ID
        """
        gate_id = f"{project_id}_{phase}_{datetime.utcnow().timestamp()}"

        gate = {
            "id": gate_id,
            "project_id": project_id,
            "phase": phase,
            "artifact": artifact,
            "status": "pending",
            "created_at": datetime.utcnow(),
        }

        self._pending_approvals[gate_id] = gate

        logger.info(
            "Approval gate created",
            gate_id=gate_id,
            project_id=project_id,
            phase=phase,
        )

        # Notify via WebSocket
        if self.ws_manager:
            await self.ws_manager.broadcast(project_id, {
                "type": "approval_required",
                "phase": phase,
                "artifact_preview": self._create_preview(artifact),
            })

        return gate_id

    async def approve(
        self,
        project_id: str,
        feedback: Optional[str] = None,
    ) -> bool:
        """Approve the pending gate for a project."""
        gate = self._find_pending_gate(project_id)
        if not gate:
            return False

        gate["status"] = "approved"
        gate["feedback"] = feedback
        gate["resolved_at"] = datetime.utcnow()

        logger.info(
            "Approval gate approved",
            gate_id=gate["id"],
            project_id=project_id,
        )

        return True

    async def reject(
        self,
        project_id: str,
        feedback: str,
    ) -> bool:
        """Reject the pending gate for a project."""
        gate = self._find_pending_gate(project_id)
        if not gate:
            return False

        gate["status"] = "rejected"
        gate["feedback"] = feedback
        gate["resolved_at"] = datetime.utcnow()

        logger.info(
            "Approval gate rejected",
            gate_id=gate["id"],
            project_id=project_id,
            feedback=feedback,
        )

        return True

    async def get_pending_gate(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get pending approval gate for a project."""
        return self._find_pending_gate(project_id)

    def _find_pending_gate(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Find pending gate for project."""
        for gate in self._pending_approvals.values():
            if gate["project_id"] == project_id and gate["status"] == "pending":
                return gate
        return None

    def _create_preview(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Create a preview of the artifact for display."""
        # Return a simplified version for the UI
        return {
            "type": artifact.get("type", "unknown"),
            "summary": artifact.get("summary", ""),
            "key_points": artifact.get("key_points", [])[:5],
        }
