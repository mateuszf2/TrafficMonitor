import math
from collections import defaultdict

carStartTimes = defaultdict(lambda: -1)  # Default to -1 indicating no start detected
carReactionWarnings = []  # To store warnings about delayed starts
reactionThreshold = 1  # Threshold for acceptable reaction time in seconds (adjust as needed)
def calculate_seconds_from_frames(timeTaken, frame_rate=30):
    return timeTaken / frame_rate

def calculate_reaction_time(id ,cx,cy,carPositions,carsGroupedByArr,currentFrame,lightGreenFrame ):
    global carStartTimes,reactionThreshold,carReactionWarnings
    # Record when the car starts moving
    if carStartTimes[id] == -1:
        # Check if the car is moving by comparing the current position with the last frame's position
        if id in carPositions and len(carPositions[id]) > 1:
            prev_pos = carPositions[id][-2]
            if math.hypot(cx - prev_pos[0], cy - prev_pos[1]) > 3:  #  Adjust threshold in pixels
                #print(math.hypot(cx - prev_pos[0], cy - prev_pos[1]) )
                carStartTimes[id] = currentFrame

                laneId=-1
                # Determine if the start time is acceptable
                if any(id == car[0] for group in carsGroupedByArr for car in group):
                    # Iterate through each traffic lane (group of cars)
                    for lane in carsGroupedByArr:
                        laneId+=1
                        # Find the car's position in its lane
                        for idx, (trackId, cy) in enumerate(lane):
                            if trackId == id:
                                # Check if the car is the first in its lane (the one with the smallest 'cy')
                                if idx == 0:  # The first car in the lane
                                    timeTaken = currentFrame - lightGreenFrame[laneId]
                                    timeTaken=calculate_seconds_from_frames(timeTaken)
                                    if timeTaken > reactionThreshold:
                                        carReactionWarnings.append((id, timeTaken))
                                        print(
                                            f"Warning: Car {id} took too long {timeTaken}s to start after light turned green!")
                                else:
                                    # For subsequent cars, check the start time of tqhe car ahead in the lane
                                    frontCarId = lane[idx - 1][0]  # Get the trackId of the car ahead
                                    if carStartTimes[frontCarId] > 0:  # Ensure the front car has started
                                        timeTaken = currentFrame - carStartTimes[frontCarId]
                                        timeTaken = calculate_seconds_from_frames(timeTaken)
                                        if timeTaken > reactionThreshold:
                                            carReactionWarnings.append((id, timeTaken))
                                            print(
                                                f"Warning: Car {id} took too long {timeTaken}s to start after the front car!")
                                break

