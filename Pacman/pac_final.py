import pygame
import os
from board import boards
import copy
import math
import random

pygame.init()

# Create screen
window = pygame.display.set_mode((980, 920))
WIDTH = 1000
HEIGHT = 950
level = copy.deepcopy(boards)
color = 'blue'
PI = math.pi

# Set framerate
clock = pygame.time.Clock()
FPS = 60

# Title and Icon
pygame.display.set_caption("Replica Pac-Man")
icon = pygame.image.load('game_logo.png')
pygame.display.set_icon(icon)

# Defining player action variables
moving_left = False
moving_right = False
moving_up = False
moving_down = False

class Animation:
    def __init__(self, folder_path, frame_rate):
        self.images = self.load_images_from_folder(folder_path)
        self.frame_rate = frame_rate
        self.current_frame = 0
        self.time_since_last_frame = 0

    def load_images_from_folder(self, folder_path):
        images = []
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith('.png'):
                img = pygame.image.load(os.path.join(folder_path, filename))
                # Scale the image
                width, height = img.get_size()
                scaled_img = pygame.transform.scale(img, (int(width * 2), int(height * 2)))
                images.append(scaled_img)
        return images

    def update(self, dt):
        self.time_since_last_frame += dt
        if self.time_since_last_frame >= self.frame_rate:
            self.current_frame = (self.current_frame + 1) % len(self.images)
            self.time_since_last_frame = 0

    def draw(self, surface, position, direction):
        image = self.images[self.current_frame]
        if direction == 'left':
            image = pygame.transform.flip(image, True, False)
        elif direction == 'up':
            image = pygame.transform.rotate(image, 90)
        elif direction == 'down':
            image = pygame.transform.rotate(image, -90)
        surface.blit(image, position)

class Dot(pygame.sprite.Sprite):
    def __init__(self, x, y, is_power_dot=False):
        pygame.sprite.Sprite.__init__(self)
        self.is_power_dot = is_power_dot
        self.radius = 10 if is_power_dot else 4
        self.color = 'white'
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        self.eaten = False

    def draw(self, surface):
        if not self.eaten:
            pygame.draw.circle(surface, self.color, self.rect.center, self.radius)

# Player Pac-man
class Pacman(pygame.sprite.Sprite):
    def __init__(self, playerX, playerY, speed, animation):
        pygame.sprite.Sprite.__init__(self)
        self.speed = speed
        self.animation = animation
        self.rect = self.animation.images[0].get_rect()
        self.rect.center = (playerX, playerY)
        self.direction = 'right'  # Default direction
        self.moving = False
        self.score = 0  # Initialize score
        self.power_mode = False  # To track if Pac-Man is in power mode

    def move(self, moving_left, moving_right, moving_up, moving_down):
        # Reset movement variables
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            self.direction = 'left'
            self.moving = True
        
        if moving_right:
            dx = self.speed
            self.direction = 'right'
            self.moving = True

        if moving_up:
            dy = -self.speed
            self.direction = 'up'
            self.moving = True
        
        if moving_down:
            dy = self.speed
            self.direction = 'down'
            self.moving = True

        # Check for collision with walls or board boundaries
        if not self.check_collision(dx, dy):
            # Update rectangle position if no collision
            self.rect.x += dx
            self.rect.y += dy
        
        # Teleport Pac-Man if he goes off the screen
        self.teleport()

        # Check for collisions with dots
        self.eat_dot()

    def eat_dot(self):
        # Calculate current grid position based on Pac-Man's position
        grid_x = self.rect.centerx // (WIDTH // 30)
        grid_y = self.rect.centery // ((HEIGHT - 50) // 32)

        # Check if the current grid position contains a dot or power dot
        if level[grid_y][grid_x] in [1, 2]:
            if level[grid_y][grid_x] == 1:
                self.score += 10  # Regular dot
            elif level[grid_y][grid_x] == 2:
                self.score += 50  # Power dot
                self.power_mode = True  # Activate power mode
            level[grid_y][grid_x] = 0  # Remove dot from the board

    def check_collision(self, dx, dy):
        # Create a smaller rectangle for collision detection
        collision_rect = self.rect.inflate(-10, -20)  # Reduce the size by 10 pixels on each side
        collision_rect.x += dx
        collision_rect.y += dy

        # Board boundaries (assuming 0, 0 is the top-left corner)
        if collision_rect.left < 0 or collision_rect.right > WIDTH or collision_rect.top < 0 or collision_rect.bottom > HEIGHT:
            return True

        # Check collision with walls in the level
        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30
        for i in range(len(level)):
            for j in range(len(level[i])):
                if level[i][j] in (3, 4, 5, 6, 7, 8):  # Consider these as wall types
                    wall_rect = pygame.Rect(j * num2, i * num1, num2, num1)
                    if collision_rect.colliderect(wall_rect):
                        return True

        return False

    def teleport(self):
        # Teleport Pac-Man to the opposite side if he goes off-screen
        if self.rect.left < 0:
            self.rect.right = WIDTH
        elif self.rect.right > WIDTH:
            self.rect.left = 0

        if self.rect.top < 0:
            self.rect.bottom = HEIGHT
        elif self.rect.bottom > HEIGHT:
            self.rect.top = 0

    def update(self, dt):
        if self.moving:
            self.animation.update(dt)
        self.moving = False

    def draw(self):
        self.animation.draw(window, self.rect.topleft, self.direction)

    def check_ghost_collision(self, ghosts):
        for ghost in ghosts:
            if self.rect.colliderect(ghost.rect):
                if self.power_mode:
                    # Pac-Man can eat the ghost
                    ghosts.remove(ghost)
                    self.score += 200  # Bonus score for eating a ghost
                else:
                    # Handle game over or collision with a non-power mode
                    print("Game Over! Pac-Man collided with a ghost.")

    def reset_power_mode(self):
        self.power_mode = False

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, folder_path):
        pygame.sprite.Sprite.__init__(self)
        self.images = self.load_images_from_folder(folder_path)
        self.rect = self.images['right'].get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.direction = 'right'

    def load_images_from_folder(self, folder_path):
        images = {}
        image_files = sorted(os.listdir(folder_path))
        directions = ['right', 'left', 'up', 'down']

        for i, direction in enumerate(directions):
            image = pygame.image.load(os.path.join(folder_path, image_files[i]))
            images[direction] = pygame.transform.scale(image, (40, 40))  # Scale image if necessary

        return images

    def move(self):
        dx, dy = 0, 0
        
        if self.direction == 'left':
            dx = -self.speed
        elif self.direction == 'right':
            dx = self.speed
        elif self.direction == 'up':
            dy = -self.speed
        elif self.direction == 'down':
            dy = self.speed
        
        # Change direction randomly
        if random.randint(0, 100) < 10:  # 10% chance to change direction
            self.direction = random.choice(['left', 'right', 'up', 'down'])
        
        # Check for collision with walls or board boundaries
        if not self.check_collision(dx, dy):
            self.rect.x += dx
            self.rect.y += dy

    def check_collision(self, dx, dy):
        collision_rect = self.rect.inflate(-20, -20)  # Smaller collision rect
        collision_rect.x += dx
        collision_rect.y += dy

        if collision_rect.left < 0 or collision_rect.right > WIDTH or collision_rect.top < 0 or collision_rect.bottom > HEIGHT:
            return True

        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30
        for i in range(len(level)):
            for j in range(len(level[i])):
                if level[i][j] in (3, 4, 5, 6, 7, 8):
                    wall_rect = pygame.Rect(j * num2, i * num1, num2, num1)
                    if collision_rect.colliderect(wall_rect):
                        return True

        return False

    def update(self):
        self.move()

    def draw(self, surface):
        # Draw the ghost with the correct image based on its current direction
        surface.blit(self.images[self.direction], self.rect.topleft)


def draw_board():
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(window, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            elif level[i][j] == 2:
                pygame.draw.circle(window, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
            elif level[i][j] == 3:
                pygame.draw.line(window, color, (j * num2 + (0.5 * num2), i * num1),
                                 (j * num2 + (0.5 * num2), i * num1 + num1), 3)
            elif level[i][j] == 4:
                pygame.draw.line(window, color, (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            elif level[i][j] == 5:
                pygame.draw.arc(window, color, pygame.Rect(j * num2 - (num2 * 0.4) - 2, i * num1 + (0.5 * num1), num2, num1),
                                0, PI / 2, 3)
            elif level[i][j] == 6:
                pygame.draw.arc(window, color,
                                pygame.Rect(j * num2 + (num2 * 0.5), i * num1 + (0.5 * num1), num2, num1), PI / 2, PI, 3)
            elif level[i][j] == 7:
                pygame.draw.arc(window, color, pygame.Rect(j * num2 + (num2 * 0.5), i * num1 - (0.4 * num1), num2, num1), PI,
                                3 * PI / 2, 3)
            elif level[i][j] == 8:
                pygame.draw.arc(window, color,
                                pygame.Rect(j * num2 - (num2 * 0.4) - 2, i * num1 - (0.4 * num1), num2, num1), 3 * PI / 2,
                                2 * PI, 3)
            elif level[i][j] == 9:
                pygame.draw.line(window, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)

# Initialize Animation with folder path containing images
folder_path = r'C:\\Users\\Castr\\OneDrive\\Desktop\\pac_animation'  # Replace with your actual folder path
animation = Animation(folder_path, 100)

# Initialize Player
player = Pacman(470, 515, 5, animation)
ghosts = [
    Ghost(500, 380, 3, r'C:\\Users\\Castr\\OneDrive\\Desktop\\redghost'),   # Ghost 1 at position (300, 300) with red color
    Ghost(500, 460, 3, r'C:\\Users\\Castr\\OneDrive\\Desktop\\pinkghost'),  # Ghost 2 at position (400, 400) with pink color
    Ghost(500, 460, 3, r'C:\\Users\\Castr\\OneDrive\\Desktop\\cyanghost'),  # Ghost 3 at position (500, 300) with cyan color
    Ghost(500, 450, 3, r'C:\\Users\\Castr\\OneDrive\\Desktop\\orangeghost') # Ghost 4 at position (600, 400) with orange color
]
run = True
while run:
    dt = clock.tick(FPS)
    # Set background color
    window.fill((0, 0, 0))
    draw_board()

    player.move(moving_left, moving_right, moving_up, moving_down)
    player.update(dt)
    player.draw()
    
    for ghost in ghosts:
        ghost.update()  # Update ghost's position towards Pac-Man
        ghost.draw(window)

    player.check_ghost_collision(ghosts)
    # Display the score
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f'Score: {player.score}', True, 'white')
    window.blit(score_text, (10, 10))

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                moving_left = True
            if event.key in [pygame.K_RIGHT, pygame.K_d]:
                moving_right = True
            if event.key in [pygame.K_UP, pygame.K_w]:
                moving_up = True
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                moving_down = True
            if event.key == pygame.K_ESCAPE:
                run = False

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                moving_left = False
            if event.key in [pygame.K_RIGHT, pygame.K_d]:
                moving_right = False
            if event.key in [pygame.K_UP, pygame.K_w]:
                moving_up = False
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                moving_down = False

pygame.quit()