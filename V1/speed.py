class SpeedCalculator:

    def __init__(self):
        self.prev_position = None
        self.prev_time = None

    def calculate_speed(self, current_position, current_time):
        if self.prev_position is None or self.prev_time is None:
            self.prev_position = current_position
            self.prev_time = current_time
            return 0
        
        distance_moved = abs(current_position[1] - self.prev_position[1])
        time_elapsed = current_time - self.prev_time

        if time_elapsed != 0:
            speed = distance_moved / time_elapsed
        else:
            speed = 0

        self.prev_position = current_position
        self.prev_time = current_time

        return speed
