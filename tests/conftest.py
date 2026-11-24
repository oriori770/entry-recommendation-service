import pytest
from datetime import datetime
from bson import ObjectId

@pytest.fixture
def sample_participant_doc():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "ישראל",
        "family": "ישראלי",
        "barcode": "abc-123-xyz",
        "phone": "0501234567",
        "city": "ירושלים",
        "groupType": "anash",
        "isApproved": True,
        "createdAt": datetime(2026, 9, 1, 10, 0, 0),
        "updatedAt": datetime(2026, 9, 1, 10, 0, 0)
    }

@pytest.fixture
def sample_event_doc():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "name": "טורניר קט-רגל",
        "date": datetime(2026, 10, 5, 18, 30, 0),
        "description": "טורניר ספורט ישיבתי",
        "isActive": True
    }

@pytest.fixture
def sample_entry_doc():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "participantId": ObjectId("507f1f77bcf86cd799439011"),
        "eventId": ObjectId("507f1f77bcf86cd799439022"),
        "scannerId": ObjectId("507f1f77bcf86cd799439099"),
        "entryTime": datetime(2026, 10, 5, 18, 35, 0),
        "method": "barcode"
    }
