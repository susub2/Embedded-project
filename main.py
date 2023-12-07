from PIL import Image, ImageDraw, ImageFont
import time
import random
from colorsys import hsv_to_rgb
import numpy as np
from digitalio import DigitalInOut, Direction
from adafruit_rgb_display import st7789
import board

class Joystick:
    def __init__(self):
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.BAUDRATE = 24000000

        self.spi = board.SPI()
        self.disp = st7789.ST7789(
                    self.spi,
                    height=240,
                    y_offset=80,
                    rotation=180,
                    cs=self.cs_pin,
                    dc=self.dc_pin,
                    rst=self.reset_pin,
                    baudrate=self.BAUDRATE,
                    )

        # Input pins:
        self.button_A = DigitalInOut(board.D5)
        self.button_A.direction = Direction.INPUT

        self.button_B = DigitalInOut(board.D6)
        self.button_B.direction = Direction.INPUT

        self.button_L = DigitalInOut(board.D27)
        self.button_L.direction = Direction.INPUT

        self.button_R = DigitalInOut(board.D23)
        self.button_R.direction = Direction.INPUT

        self.button_U = DigitalInOut(board.D17)
        self.button_U.direction = Direction.INPUT

        self.button_D = DigitalInOut(board.D22)
        self.button_D.direction = Direction.INPUT

        self.button_C = DigitalInOut(board.D4)
        self.button_C.direction = Direction.INPUT

        # Turn on the Backlight
        self.backlight = DigitalInOut(board.D26)
        self.backlight.switch_to_output()
        self.backlight.value = True

        # Create blank image for drawing.
        # Make sure to create image with mode 'RGB' for color.
        self.width = self.disp.width
        self.height = self.disp.height

class Character:
    def __init__(self, width, height):
        self.appearance = 'circle'
        self.state = None
        self.width = width
        self.height = height
        self.position = np.array([width/2 - 20, height - 40, width/2 + 20, height - 20])
        self.outline = "#FFFFFF"

    def move(self, command=None):
        if command is None:
            self.state = None
            self.outline = "#FFFFFF"
        else:
            self.state = 'move'
            self.outline = "#FF0000"

            if command == 'left_pressed':
                # 좌우 이동 구현
                self.position[0] = max(0, self.position[0] - 5)
                self.position[2] = max(0, self.position[2] - 5)
            elif command == 'right_pressed':
                # 좌우 이동 구현
                self.position[0] = min(self.width, self.position[0] + 5)
                self.position[2] = min(self.width, self.position[2] + 5)
            
class Enemy:
    def __init__(self, spawn_position):
        self.appearance = 'circle'
        self.state = 'alive'
        self.position = [spawn_position[0] - 25, spawn_position[1] - 25, spawn_position[0] + 25, spawn_position[1] + 25]
        self.outline = "#00FF00"

    def move_down(self, speed):
        self.position[1] += speed
        self.position[3] += speed

def spawn_enemy(width, height):
    spawn_x = np.random.randint(0, width)
    spawn_y = 0
    return Enemy([spawn_x, spawn_y])

def check_collision(character, enemy):
    char_x1, char_y1, char_x2, char_y2 = character.position
    enemy_x1, enemy_y1, enemy_x2, enemy_y2 = enemy.position

    if char_x2 > enemy_x1 and char_x1 < enemy_x2 and char_y2 > enemy_y1 and char_y1 < enemy_y2:
        return True
    else:
        return False

def display_message(disp, message):
    # 화면에 메시지를 표시하는 함수
    WIDTH = disp.width
    HEIGHT = disp.height

    # 화면 초기화
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 255, 255))

    # 메시지 표시
    font = ImageFont.load_default()
    text_width, text_height = draw.textsize(message, font=font)
    text_position = ((WIDTH - text_width) // 2, (HEIGHT - text_height) // 2)
    draw.text(text_position, message, font=font, fill=(0, 0, 0))

    # 화면 갱신
    disp.image(image)

def main():
    start_time = time.time()
    game_duration = 120
    win_condition = False

    joystick = Joystick()

    # Adafruit RGB Display 초기화
    spi = board.SPI()
    tft_cs = DigitalInOut(board.CE0)
    tft_dc = DigitalInOut(board.D25)
    tft_reset = DigitalInOut(board.D24)
    disp = st7789.ST7789(spi, width=240, height=240, x_offset=0, y_offset=80, rotation=180,
                         cs=tft_cs, dc=tft_dc, rst=tft_reset, baudrate=24000000)
    
    # 캐릭터 초기화
    my_circle = Character(disp.width, disp.height)
    
    # 초기적 생성
    active_enemies = []

    while True:
        command = None
        if not joystick.button_U.value:
            command = 'up_pressed'
        elif not joystick.button_D.value:
            command = 'down_pressed'
        elif not joystick.button_L.value:
            command = 'left_pressed'
        elif not joystick.button_R.value:
            command = 'right_pressed'
        else:
            command = None

        my_circle.move(command)

        # Enemy spawning logic
        if len(active_enemies) < 3 and np.random.rand() < 0.03:  # Adjust the probability as needed
            new_enemy = spawn_enemy(disp.width, disp.height)
            active_enemies.append(new_enemy)

        # Update active enemies
        for enemy in active_enemies:
            enemy.move_down(12)

        # Remove enemies that are out of the screen
        active_enemies = [enemy for enemy in active_enemies if enemy.position[1] < disp.height]

        # Check collision with any of the active enemies
        collision = any(check_collision(my_circle, enemy) for enemy in active_enemies)
        if collision:
            display_message(disp, "You Lose")
            break

        elapsed_time = time.time() - start_time
        if elapsed_time >= game_duration:
            win_condition = True
            display_message(disp, "Congratulations! You Win!")
            break

        # Draw characters and enemies on the screen
        image = Image.new("RGB", (disp.width, disp.height))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, disp.width, disp.height), fill=(255, 255, 255))
        draw.ellipse(tuple(my_circle.position), outline=my_circle.outline, fill=(0, 0, 0))

        for enemy in active_enemies:
            draw.ellipse(tuple(enemy.position), outline=enemy.outline, fill=(0, 255, 0))

        # Display time left
        time_left = max(0, int(game_duration - elapsed_time))
        font = ImageFont.load_default()
        draw.text((disp.width - 120, 10), f"Time Left: {time_left} s", fill=(0, 0, 0), font=font)

        # Update the screen
        disp.image(image)
        time.sleep(0.05)

    print("Game Over")

if __name__ == '__main__':
    main()
