from abc import ABC, abstractmethod
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from datetime import datetime

# Observer Pattern Interfaces
class Observer(ABC):
    """Abstract Observer interface"""
    
    @abstractmethod
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        pass

class Subject(ABC):
    """Abstract Subject interface"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    async def notify(self, event_type: str, data: Dict[str, Any]) -> None:
        for observer in self._observers:
            await observer.update(event_type, data)

# Concrete Observers
class EmailNotificationObserver(Observer):
    """Observer that handles email notifications"""
    
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        print(f"📧 EMAIL: {event_type} - Sending email notification")
        print(f"   Data: {json.dumps(data, indent=2)}")

class LoggingObserver(Observer):
    """Observer that logs events"""
    
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        print(f"📝 LOG: [{timestamp}] {event_type}")
        print(f"   Data: {json.dumps(data, indent=2)}")

class SlackNotificationObserver(Observer):
    """Observer that sends Slack notifications"""
    
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        print(f"💬 SLACK: {event_type} - Sending Slack notification")
        print(f"   Data: {json.dumps(data, indent=2)}")

class AnalyticsObserver(Observer):
    """Observer that tracks analytics"""
    
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        print(f"📊 ANALYTICS: Tracking event '{event_type}'")
        print(f"   Metrics: user_id={data.get('user_id')}, timestamp={datetime.now()}")

# Concrete Subject - User Service
class UserService(Subject):
    """User service that notifies observers of user events"""
    
    def __init__(self):
        super().__init__()
        self.users: Dict[int, Dict] = {}
        self.next_id = 1
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = self.next_id
        self.next_id += 1
        
        user = {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "created_at": datetime.now().isoformat()
        }
        
        self.users[user_id] = user
        
        # Notify observers
        await self.notify("USER_CREATED", {
            "user_id": user_id,
            "user_data": user,
            "timestamp": datetime.now().isoformat()
        })
        
        return user
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        if user_id not in self.users:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_data = self.users[user_id].copy()
        self.users[user_id].update(user_data)
        
        # Notify observers
        await self.notify("USER_UPDATED", {
            "user_id": user_id,
            "old_data": old_data,
            "new_data": self.users[user_id],
            "timestamp": datetime.now().isoformat()
        })
        
        return self.users[user_id]
    
    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.users:
            raise HTTPException(status_code=404, detail="User not found")
        
        deleted_user = self.users.pop(user_id)
        
        # Notify observers
        await self.notify("USER_DELETED", {
            "user_id": user_id,
            "deleted_user": deleted_user,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "User deleted successfully", "user": deleted_user}
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.users:
            raise HTTPException(status_code=404, detail="User not found")
        return self.users[user_id]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        return list(self.users.values())

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: str = None
    email: str = None

# FastAPI Application
app = FastAPI(title="Observer Pattern Demo", version="1.0.0")

# Initialize service and observers
user_service = UserService()

# Create observers
email_observer = EmailNotificationObserver()
logging_observer = LoggingObserver()
slack_observer = SlackNotificationObserver()
analytics_observer = AnalyticsObserver()

# Attach observers to the service
user_service.attach(email_observer)
user_service.attach(logging_observer)
user_service.attach(slack_observer)
user_service.attach(analytics_observer)

# API Endpoints
@app.post("/users", response_model=dict)
async def create_user(user: UserCreate):
    """Create a new user - triggers observer notifications"""
    return await user_service.create_user(user.dict())

@app.get("/users/{user_id}", response_model=dict)
async def get_user(user_id: int):
    """Get a user by ID"""
    return user_service.get_user(user_id)

@app.get("/users", response_model=list)
async def get_all_users():
    """Get all users"""
    return user_service.get_all_users()

@app.put("/users/{user_id}", response_model=dict)
async def update_user(user_id: int, user: UserUpdate):
    """Update a user - triggers observer notifications"""
    update_data = {k: v for k, v in user.dict().items() if v is not None}
    return await user_service.update_user(user_id, update_data)

@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: int):
    """Delete a user - triggers observer notifications"""
    return await user_service.delete_user(user_id)

@app.get("/")
async def root():
    """Root endpoint with usage instructions"""
    return {
        "message": "Observer Pattern Demo API",
        "instructions": {
            "create_user": "POST /users with {name, email}",
            "get_user": "GET /users/{id}",
            "update_user": "PUT /users/{id} with {name?, email?}",
            "delete_user": "DELETE /users/{id}",
            "get_all_users": "GET /users"
        },
        "note": "Check console output to see observer notifications in action!"
    }

# Example of dynamic observer management
@app.post("/observers/detach/{observer_type}")
async def detach_observer(observer_type: str):
    """Dynamically detach an observer"""
    observer_map = {
        "email": email_observer,
        "logging": logging_observer,
        "slack": slack_observer,
        "analytics": analytics_observer
    }
    
    if observer_type in observer_map:
        user_service.detach(observer_map[observer_type])
        return {"message": f"{observer_type} observer detached"}
    else:
        raise HTTPException(status_code=400, detail="Invalid observer type")

@app.post("/observers/attach/{observer_type}")
async def attach_observer(observer_type: str):
    """Dynamically attach an observer"""
    observer_map = {
        "email": email_observer,
        "logging": logging_observer,
        "slack": slack_observer,
        "analytics": analytics_observer
    }
    
    if observer_type in observer_map:
        observer = observer_map[observer_type]
        if observer not in user_service._observers:
            user_service.attach(observer)
            return {"message": f"{observer_type} observer attached"}
        else:
            return {"message": f"{observer_type} observer already attached"}
    else:
        raise HTTPException(status_code=400, detail="Invalid observer type")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
