print("=" * 60)
print("RUNNING run_full_analysis.py")
print("=" * 60)
import subprocess
result1 = subprocess.run(['.venv\\Scripts\\python', 'run_full_analysis.py'], 
                         capture_output=True, text=True, timeout=60)
lines = result1.stdout.split('\n')
for line in lines[:25]:
    print(line)

print("\n" + "=" * 60)
print("RUNNING debug_train.py (engine.py)")
print("=" * 60)
result2 = subprocess.run(['.venv\\Scripts\\python', 'debug_train.py'], 
                         capture_output=True, text=True, timeout=60)
lines = result2.stdout.split('\n')
for line in lines[:25]:
    print(line)
