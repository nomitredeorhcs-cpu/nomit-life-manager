#!/usr/bin/env python3
"""
Simple HTTP server for Nomit WebApp
No Flask needed - uses built-in http.server
"""

import json
import os
import http.server
import socketserver
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import threading

import os
PORT = int(os.environ.get("PORT", 8081))  # Render uses $PORT, default to 8081 locally
DATA_FILE = "data/tracker.json"

class NomitRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # Serve static files
        if parsed.path.startswith('/static/') or parsed.path == '/':
            return super().do_GET()
        
        # API endpoints
        if parsed.path == '/api/dashboard':
            self.send_dashboard()
        elif parsed.path == '/api/habits':
            self.send_habits()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path.startswith('/api/habits/') and parsed.path.endswith('/complete'):
            habit_id = parsed.path.split('/')[-2]
            self.complete_habit(habit_id)
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        
        # Default data
        default_data = {
            "habits": [
                {
                    "id": "habit_morning_supp",
                    "name": "Supplements morgens nehmen",
                    "bereich": "Gesundheit",
                    "typ": "Daily",
                    "streak": 0,
                    "last_completed": None,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "habit_evening_supp",
                    "name": "Supplements abends nehmen",
                    "bereich": "Gesundheit",
                    "typ": "Daily",
                    "streak": 0,
                    "last_completed": None,
                    "created_at": datetime.now().isoformat()
                }
            ],
            "completions": [],
            "settings": {
                "daily_budget": 40,
                "australia_target": "2027-01-01"
            }
        }
        
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(default_data, f, indent=2)
        
        return default_data
    
    def save_data(self, data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def send_dashboard(self):
        data = self.load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate today's completions
        today_completions = [
            c for c in data["completions"]
            if c.get("date") == today
        ]
        
        # Calculate Australia countdown
        australia_date = datetime(2027, 1, 1)
        days_to_australia = (australia_date - datetime.now()).days
        
        # Prepare habits with today's status
        habits_with_status = []
        for habit in data["habits"]:
            completed_today = any(
                c.get("habit_id") == habit["id"] and c.get("date") == today
                for c in data["completions"]
            )
            habits_with_status.append({
                **habit,
                "completed_today": completed_today
            })
        
        response = {
            "habits": habits_with_status,
            "today_completions": len(today_completions),
            "total_habits": len(data["habits"]),
            "days_to_australia": days_to_australia,
            "daily_budget": data["settings"]["daily_budget"],
            "updated_at": datetime.now().isoformat()
        }
        
        self.send_json(response)
    
    def send_habits(self):
        data = self.load_data()
        self.send_json(data["habits"])
    
    def complete_habit(self, habit_id):
        data = self.load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Find habit
        habit = None
        for h in data["habits"]:
            if h["id"] == habit_id:
                habit = h
                break
        
        if not habit:
            self.send_json({"error": "Habit not found"}, 404)
            return
        
        # Check if already completed today
        already_completed = any(
            c.get("habit_id") == habit_id and c.get("date") == today
            for c in data["completions"]
        )
        
        if already_completed:
            self.send_json({
                "message": f"Habit '{habit['name']}' already completed today",
                "streak": habit["streak"]
            })
            return
        
        # Add completion
        completion = {
            "habit_id": habit_id,
            "habit_name": habit["name"],
            "date": today,
            "timestamp": datetime.now().isoformat()
        }
        
        data["completions"].append(completion)
        
        # Update streak
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        completed_yesterday = any(
            c.get("habit_id") == habit_id and c.get("date") == yesterday
            for c in data["completions"]
        )
        
        if completed_yesterday:
            habit["streak"] += 1
        else:
            habit["streak"] = 1
        
        habit["last_completed"] = today
        self.save_data(data)
        
        self.send_json({
            "message": f"Habit '{habit['name']}' completed!",
            "streak": habit["streak"],
            "completed_today": True
        })

def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    handler = NomitRequestHandler
    handler.extensions_map = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '': 'application/octet-stream',
    }
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🚀 Nomit WebApp running on http://localhost:{PORT}")
        print(f"📊 Dashboard: http://localhost:{PORT}/")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()