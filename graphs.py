import matplotlib.pyplot as plt

# Data (simulated experimental results)
requests = [5, 10, 15]

fcfs = [3.5, 3.8, 4.2]
priority = [3.1, 3.3, 3.6]
adaptive = [2.5, 2.6, 2.8]

# Plot
plt.figure()
plt.plot(requests, fcfs, marker='o', label='FCFS')
plt.plot(requests, priority, marker='o', label='Priority')
plt.plot(requests, adaptive, marker='o', label='Adaptive')

# Labels
plt.xlabel("Number of Requests")
plt.ylabel("Response Time (seconds)")
plt.title("Scheduler Performance Comparison")
plt.legend()

# Show graph
plt.show()