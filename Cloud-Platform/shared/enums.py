from enum import Enum


class TaskStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_DISPATCH = "PENDING_DISPATCH"
    DISPATCHED = "DISPATCHED"
    ROBOT_ACKED = "ROBOT_ACKED"
    RUNNING = "RUNNING"
    DATA_UPLOADING = "DATA_UPLOADING"
    DATA_READY = "DATA_READY"
    ANALYZING = "ANALYZING"
    CANCELLING = "CANCELLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskEventType(str, Enum):
    CREATED = "created"
    DISPATCHED = "dispatched"
    DISPATCH_FAILED = "dispatch_failed"
    ROBOT_ACK = "robot_ack"
    STATUS = "status"
    PROGRESS = "progress"
    HEARTBEAT = "heartbeat"
    EXCEPTION = "exception"
    PROTOCOL_REJECTED = "protocol_rejected"
    DATA_SESSION_CREATED = "data_session_created"
    DATA_UPLOADED = "data_uploaded"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_FINISHED = "analysis_finished"
    ANALYSIS_FAILED = "analysis_failed"
    RETRY_REQUESTED = "retry_requested"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


class RobotStatus(str, Enum):
    IDLE = "IDLE"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    BUSY = "BUSY"
    ERROR = "ERROR"


class RobotCommandStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACKED = "ACKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class AssetType(str, Enum):
    IMAGE = "IMAGE"
    DEPTH = "DEPTH"
    POINT_CLOUD = "POINT_CLOUD"
    RESULT = "RESULT"
    REPORT = "REPORT"
    OTHER = "OTHER"


class AnalysisJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
