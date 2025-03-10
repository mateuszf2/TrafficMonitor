# TrafficMonitor :blue_car:

TrafficMonitor is a project for monitoring and analyzing traffic flow.


[TrafficMonitor1.webm](https://github.com/user-attachments/assets/94d2e583-56f6-4bd1-9ce0-38054adb7fd3)

[TrafficMonitor2.webm](https://github.com/user-attachments/assets/91dd2340-b845-4bf8-ae4f-bf18e8a714d2)

![TrafficMonitor](https://github.com/user-attachments/assets/f55a68ef-f2ea-489c-a9f2-a86d3a5a202d)



## Features :star2:

- Detecting cars and traffic lights using AI YOLO models 
- Estimating roadway users' speeds, distances between cars 
- Dividing cars by selected traffic lanes 
- Estimating cars reaction time when starting from traffic lights
- Making a photo of the car driving while passing on the red light
- Storing the data in MySQL database
- Analyzing data on website panel

![TrafficMonitorPanel1](https://github.com/user-attachments/assets/6d9e5ec0-b864-4d65-a8a3-1cce9f37d89b)
![TrafficMonitorPanel2](https://github.com/user-attachments/assets/fd233bdb-00a4-4a33-b277-0237d6fb7954)
![TrafficMonitorPanel3](https://github.com/user-attachments/assets/e19d5958-4de7-453f-8b75-d77577a8db43)
![TrafficMonitorPanel4](https://github.com/user-attachments/assets/b3b83979-f89d-4f34-a24d-b6e5535b7280)


## Installation :hammer_and_wrench:
TrafficMonitor requires Python 3.10+ to run.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install libraries. This process may take some time.

What you need:
- sort file for tracker (https://github.com/abewley/sort/blob/master/sort.py)
- object detection model for cars and traffic lights (https://docs.ultralytics.com/models/yolov8/#models), for traffic lights we trained the model on some dataset for better detection
- MySQL database to collect and read data
- .env file with database data
- PyTorch packages with CUDA support in order to use GPU acceleration (more below)
```bash
pip install -r requirements.txt
pip uninstall torch torchvision
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

## Usage :computer:
After running:
```bash
python TrafficMonitor.py 
```

You are able to type name of the intersection, the city and choose option if you want to load data stored for particular intersection or create and save to database new data.

![TrafficMonitor](https://github.com/user-attachments/assets/1aecfc45-6acf-4d11-8dc3-db87aa55b94a)

If you want to select new traffic lanes:
- Choose "Pasy ruchu" button, then select two endings for each lane

If you want to select new lanes for traffic lights:
- Choose "Linie swiatel" button, then select two endings for each lane

If you want to select new traffic lights:
- Choose "Sygnalizacja" button, then select the point for each light

There is also a possibility to monitor selected part of the video and that is why the fourth button ROI (Region Of Interest) is here for.

Press 'd' to run program.


## License :page_with_curl:
TrafficMonitor is licensed under the GNU General Public License v3.0

