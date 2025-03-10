# TrafficMonitor :blue_car:

TrafficMonitor is a project for monitoring and analyzing traffic flow.


[TrafficMonitor1.webm](https://github.com/user-attachments/assets/94d2e583-56f6-4bd1-9ce0-38054adb7fd3)

[TrafficMonitor2.webm](https://github.com/user-attachments/assets/91dd2340-b845-4bf8-ae4f-bf18e8a714d2)


## Features :star2:

- Detecting cars and traffic lights using AI YOLO models 
- Estimating roadway users' speeds, distances between cars 
- Dividing cars by selected traffic lanes 
- Estimating cars reaction time when starting from traffic lights
- Making a photo of the car driving while passing on the red light
- Storing the data in MySQL database
- Analyzing data on website panel


## Installation :hammer_and_wrench:
TrafficMonitor requires Python 3.10+ to run.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install libraries. This process may take some time.

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

## Usage :computer:
After running:
```bash
python TrafficMonitor.py 
```

You are able to type name of the intersection, the city and choose option if you want to load data stored for particular intersection or create and save to database new data.

![TrafficMonitor](https://github.com/user-attachments/assets/1aecfc45-6acf-4d11-8dc3-db87aa55b94a)

If you want to select new traffic lanes:
- Choose "Pasy ruchu" button and then select two endings for each lane

If you want to select new lanes for traffic lights:
- Choose "Linie swiatel" button and then select two endings for each lane

If you want to select new traffic lights:
- Choose "Sygnalizacja" button and then select the point for each light

There is also a possibility to monitor selected part of the video and that is why the fourth button ROI (Region Of Interest) is here for.


## License :page_with_curl:
TrafficMonitor is licensed under the GNU General Public License v3.0

