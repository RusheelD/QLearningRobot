import numpy as np
from random import *
import pyglet


class Robot:
    alpha = 0.1
    gamma = 0.6
    epsilon = 1
    epsilon_decay = 0.9999
    q_table = None
    actions = 7
    gen = 0

    def __init__(self):
        self.x: int = -1
        self.y: int = -1
        self.drop_off: tuple[int, int] = (-1, -1)
        self.item: tuple[int, int] = (-1, -1)
        self.done: bool = False
        self.warehouse: Warehouse = None
        self.index: int = -1
        self.has_item: bool = False

    def make_action(self, action):
        robot_locations = self.warehouse.get_robot_locations()
        if self.done:
            return 0, False
        (x, y) = (self.x, self.y)
        if (action == 0):    # Up
            if (y == 0 or (x, y - 1) in robot_locations):
                return -10, False
            else:
                (self.x, self.y) = (x, y - 1)
                return -1, False
        elif (action == 1):  # Down
            if (y == self.warehouse.size - 1 or (x, y + 1) in robot_locations):
                return -10, False
            else:
                (self.x, self.y) = (x, y + 1)
                return -1, False
        elif (action == 2):  # Left
            if (x == 0 or (x - 1, y) in robot_locations):
                return -10, False
            else:
                (self.x, self.y) = (x - 1, y)
                return -1, False
        elif (action == 3):  # Right
            if (x == self.warehouse.size - 1 or (x + 1, y) in robot_locations):
                return -10, False
            else:
                (self.x, self.y) = (x + 1, y)
                return -1, False
        elif (action == 4):  # Pick up
            if (self.has_item or self.item != (x, y)):
                return -10, False
            else:
                self.has_item = True
                self.item = (-1, -1)
                return 20, False
        elif (action == 5):  # Drop off
            if (not (self.has_item)):
                return -10, False
            elif (self.drop_off != (x, y)):
                self.has_item = False
                self.item = (x, y)
                return -10, False
            else:
                self.x = -1
                self.y = -1
                self.item = (-1, -1)
                self.drop_off = (-1, -1)
                return 20, True
        elif (action == 6):  # Wait
            return -1, False


class Warehouse:
    def __init__(self, size: int, num_robots: int):
        self.size: int = size
        self.robots: list[Robot] = [Robot() for _ in range(num_robots)]
        self.generate_robot_data()
        Robot.q_table = np.zeros((self.get_number_of_states(), Robot.actions))

    def done(self):
        for r in self.robots:
            if (not (r.done)):
                return False
        return True

    def get_number_of_states(self):
        return self.size ** 6 * 2 * (2 ** (self.size ** 2))

    def get_state(self, robot: Robot):
        state = robot.x * (self.size ** 5) * 2 * (2 ** (self.size ** 2))
        state += robot.y * (self.size ** 4) * 2 * (2 ** (self.size ** 2))
        state += robot.item[0] * (self.size ** 3) * 2 * (2 ** (self.size ** 2))
        state += robot.item[1] * (self.size ** 2) * 2 * (2 ** (self.size ** 2))
        state += robot.drop_off[0] * \
            (self.size ** 1) * 2 * (2 ** (self.size ** 2))
        state += robot.drop_off[1] * 2 * (2 ** (self.size ** 2))
        state += (1 if robot.has_item else 0) * (2 ** (self.size ** 2))
        state += self.get_obstacles(robot)
        return state

    def get_obstacles(self, robot: Robot):
        obs = 0
        for i in range(self.size ** 2):
            x = i % self.size
            y = i // self.size
            obs += (1 if (isinstance(self.get((x, y))
                    [1], Robot) and (x, y) != (robot.x, robot.y)) else 0) * (2 ** (self.size ** 2 - i - 1))
        return obs

    def get(self, position: tuple[int, int]):
        (x, y) = position
        drop_off = ''
        thing = None
        for r in self.robots:
            if (x, y) == r.drop_off:
                drop_off = 'drop_off'
        for r in self.robots:
            if (x, y) == (r.x, r.y):
                thing = r
        if (thing is None):
            for r in self.robots:
                if r.item and (x, y) == r.item:
                    thing = 'item'
        return (drop_off, thing)

    def get_view(self, position: tuple[int, int]):
        (x, y) = position
        drop_off = ('', -1)
        thing = (None, -1)
        for r in self.robots:
            if (x, y) == r.drop_off:
                drop_off = ('drop_off', r.index)
        for r in self.robots:
            if (x, y) == (r.x, r.y):
                thing = (r, r.index)
        if (thing[0] is None):
            for r in self.robots:
                if r.item and (x, y) == r.item:
                    thing = ('item', r.index)
        return (drop_off, thing)

    def get_robot_locations(self):
        loc = []
        for robot in self.robots:
            loc.append((robot.x, robot.y))
        return loc

    def generate_robot_data(self):
        self.randomize_robots()
        self.generate_new_packages()

    def randomize_robots(self):
        for i, robot in enumerate(self.robots):
            robot.index = i
            robot.warehouse = self
            robot.done = False
            robot.has_item = False
            position = (randint(0, self.size - 1),
                        randint(0, self.size - 1))
            at = self.get(position)
            while (at[0] != '' or at[1] != None):
                position = (randint(0, self.size - 1),
                            randint(0, self.size - 1))
                at = self.get(position)
            (robot.x, robot.y) = position

    def generate_new_packages(self):
        self.generate_new_items()
        self.generate_new_drop_off()

    def generate_new_items(self):
        for robot in self.robots:
            position = (randint(0, self.size - 1),
                        randint(0, self.size - 1))
            at = self.get(position)
            while (at[0] != '' or at[1] != None):
                position = (randint(0, self.size - 1),
                            randint(0, self.size - 1))
                at = self.get(position)
            robot.item = position

    def generate_new_drop_off(self):
        for robot in self.robots:
            position = (randint(0, self.size - 1),
                        randint(0, self.size - 1))
            at = self.get(position)
            while (at[0] != '' or at[1] != None):
                position = (randint(0, self.size - 1),
                            randint(0, self.size - 1))
                at = self.get(position)
            robot.drop_off = position


class UI:
    def __init__(self, warehouse: Warehouse):
        self.scale = 600
        self.window = pyglet.window.Window(self.scale, self.scale)
        self.window.set_caption("Learning Simulation")
        self.window.set_location(300, 50)
        self.window.push_handlers(self)
        self.warehouse = warehouse
        self.background_base = pyglet.image.SolidColorImagePattern(
            (255, 255, 255, 255)).create_image(self.scale, self.scale)
        self.square_size = self.scale // self.warehouse.size
        self.updatable = True
        self.speed = 4

    def on_draw(self):
        self.window.clear()
        self.background_base.blit(0, 0)

        for row in range(self.warehouse.size):
            for col in range(self.warehouse.size):

                drop_off, cell = self.warehouse.get_view((row, col))
                column = abs(self.warehouse.size - col - 1)

                index_drop_off = drop_off[1]

                index_cell = cell[1]

                if (drop_off[0] == 'drop_off'):
                    pyglet.image.SolidColorImagePattern(
                        (75, 190, 75, 255)).create_image(self.square_size, self.square_size).blit(row * self.square_size, column * self.square_size)
                    if (index_drop_off >= 0):
                        pyglet.text.Label(text=str(index_drop_off+1), bold=True, x=row * self.square_size + self.square_size / 2,
                                          y=column * self.square_size + self.square_size / 2, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center').draw()

                if (cell[0] is None):
                    continue
                if (isinstance(cell[0], Robot)):
                    if (cell[0].done):
                        continue
                    self.draw_robot(row * self.square_size,
                                    column * self.square_size)
                if (cell[0] == 'item'):
                    self.draw_item(row * self.square_size,
                                   column * self.square_size)

                if (index_cell >= 0):
                    pyglet.text.Label(text=str(index_cell+1), bold=True, x=row * self.square_size + self.square_size / 2,
                                      y=column * self.square_size + self.square_size / 2, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center').draw()

        pyglet.text.Label(text=str(Robot.gen), bold=True, x=25,
                          y=575, color=(0, 0, 0, 255)).draw()

    def draw_robot(self, row, column):
        body = pyglet.shapes.Rectangle(
            row + self.square_size / 4, column + self.square_size / 4, self.square_size / 2, self.square_size / 2, color=(100, 100, 100))
        light = pyglet.shapes.Circle(
            row + self.square_size / 2, column + self.square_size / 2, self.square_size / 8, color=(255, 0, 0))
        body.draw()
        light.draw()

    def draw_item(self, row, column):
        item = pyglet.shapes.Circle(
            row + self.square_size / 2, column + self.square_size / 2, self.square_size / 8, color=(0, 150, 255))
        item.draw()

    def on_mouse_release(self, x, y, button, modifiers):
        self.updatable = not (self.updatable)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pyglet.clock.unschedule(self.update)
        self.speed += scroll_y / 2
        if (self.speed <= 0):
            self.speed = 0.5
        pyglet.clock.schedule_interval(self.update, 1 / self.speed)

    # def on_close(self):
    #     with open('q_table.txt', 'w') as f:
    #         f.write(Robot.q_table)

    def run(self):
        while (Robot.gen < 75000):
            self.update(0)
            if self.warehouse.done():
                print(Robot.gen)
        pyglet.clock.schedule_interval(self.update, 1/self.speed)
        pyglet.app.run()

    def update(self, dt):
        if (not (self.updatable)):
            return
        if (self.warehouse.done()):
            Robot.epsilon *= Robot.epsilon_decay
            Robot.gen += 1
            self.warehouse.generate_robot_data()

        for robot in self.warehouse.robots:

            state = self.warehouse.get_state(robot)

            if (uniform(0, 1) < Robot.epsilon):
                action = randint(0, 6)
            else:
                action = np.argmax(Robot.q_table[state])
            reward, done = robot.make_action(action)

            new_state = self.warehouse.get_state(robot)
            new_state_max = np.max(Robot.q_table[new_state])

            Robot.q_table[state, action] = (1 - Robot.alpha) * Robot.q_table[state, action] + Robot.alpha * (
                reward + Robot.gamma * new_state_max - Robot.q_table[state, action])
            if (done):
                robot.done = True


UI(Warehouse(4, 3)).run()
