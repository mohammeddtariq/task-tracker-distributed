import socket
import json

def send_command(command, task=None):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 5555))
        
        payload = {"command": command, "task": task}
        client.send(json.dumps(payload).encode('utf-8'))
        
        response = client.recv(1024).decode('utf-8')
        res_json = json.loads(response)
        
        print("\n--- Server Response ---")
        if res_json["status"] == "success":
            print(f"Tasks: {res_json.get('data', [])}")
        else:
            print(f"Error: {res_json.get('message')}")
        
        client.close()
    except Exception as e:
        print(f"Could not connect to server: {e}")

def main():
    while True:
        print("\n--- Distributed To-Do Menu ---")
        print("1. View Tasks (GET)")
        print("2. Add Task (ADD)")
        print("3. Delete Task (DELETE)")
        print("4. Exit")
        
        choice = input("Select an option (1-4): ")

        if choice == '1':
            send_command("GET")
        elif choice == '2':
            new_task = input("Enter the task: ")
            send_command("ADD", new_task)
        elif choice == '3':
            del_task = input("Enter the task name to delete: ")
            send_command("DELETE", del_task)
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()

