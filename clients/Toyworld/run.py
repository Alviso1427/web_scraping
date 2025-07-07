# clients/client1/run.py
import os

def run():
    input_path = os.path.join(os.path.dirname(__file__), "input")
    output_path = os.path.join(os.path.dirname(__file__), "output")

    # Example logic: copy input file to output
    for filename in os.listdir(input_path):
        if filename.endswith(".txt"):
            with open(os.path.join(input_path, filename)) as f:
                data = f.read()

            with open(os.path.join(output_path, f"processed_{filename}"), "w") as f:
                f.write(data.upper())

    print("Client1 script completed.")
