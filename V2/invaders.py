from qlearning import QLearning
from shapes import DetectShape
import numpy as np
import random
import pygame

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

detector = DetectShape()
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")
font = pygame.font.SysFont(None, 36)
player_speed = 30
enemy_speed = 20

Q = {}
alpha = 0.01
gamma = 0.09
epsilon = 0.01
alpha_decay = 0.0999
epsilon_decay = 0.09995
total_reward = 0
max_hits = 0
EDGE_THRESHOLD = 1
iterations = 0
qlearner = QLearning(
    actions=[-1, 0, 1, 2],
    alpha=alpha,
    gamma=0.9,
    epsilon=epsilon)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([10, 10], pygame.SRCALPHA)
        pygame.draw.circle(self.image, GRAY, (5, 5), 5)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = -30

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([50, 30], pygame.SRCALPHA)
        pygame.draw.polygon(self.image, GRAY, [(25, 0), (0, 30), (50, 30)])
        self.rect = self.image.get_rect()
        self.rect.x = (WIDTH // 2) - (self.rect.width // 2)
        self.rect.y = HEIGHT - 40
        self.last_shot_time = 0

    def can_shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > 50:  # 1000 milliseconds == 1 second
            self.last_shot_time = current_time
            return True
        return False

    def update(self, override=False, direction=None):
        if not override:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= player_speed
            if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
                self.rect.x += player_speed
        else:
            if direction == 1 and self.rect.right < WIDTH:
                self.rect.x += player_speed
            elif direction == -1 and self.rect.left > 0:
                self.rect.x -= player_speed


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([40, 40])
        self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = 10 - self.rect.height
        self.speed = enemy_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.rect.y = 10 - self.rect.height


def draw_text(text, x, y):
    rendeGRAY = font.render(text, True, GRAY)
    screen.blit(rendeGRAY, (x, y))


def game_over_screen(enemy_hits):
    screen.fill(WHITE)
    draw_text("GAME OVER", WIDTH // 2 - 100, HEIGHT // 2 - 40)
    draw_text(f"Score: {enemy_hits}", WIDTH // 2 - 70, HEIGHT // 2)
    draw_text(
        "Press R to play again or Q to quit",
        WIDTH // 2 - 220, HEIGHT // 2 + 40)
    pygame.display.flip()
    waiting = True
    return True


def get_state(detector):
    enemies_pos = detector.rectangle_positions
    player_pos = detector.triangle_position
    if not enemies_pos or not player_pos:
        return None

    player_x = player_pos[2][0]
    close_to_left_edge = player_x <= EDGE_THRESHOLD
    close_to_right_edge = player_x >= (WIDTH - EDGE_THRESHOLD)
    closest_enemy = min(enemies_pos, key=lambda pos: pos[1])
    closest_enemy_x = closest_enemy[0][0]
    speed = detector.speed
    closest_enemy_direction = -1 if closest_enemy[0][0] < player_x else 1
    return (player_x, closest_enemy_x, closest_enemy[1], close_to_left_edge, close_to_right_edge, speed, closest_enemy_direction)


def choose_action(state):
    if state is None:
        return random.choice([-1, 0, 1, 2])
    return qlearner.choose_action(state)


def learn(state, action, reward, next_state):
    qlearner.learn(state, action, reward, next_state)


def main_game():
    global iterations, alpha, epsilon, total_reward, qlearner, max_hits
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    running = True
    enemy_hits = 0

    for i in range(5):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    while running:
        reward = 0
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.can_shoot():
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    all_sprites.add(bullet)
                    bullets.add(bullet)

        hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
        for hit in hits:
            enemy_hits += 1
            reward += 1000
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

        if pygame.sprite.spritecollide(player, enemies, False):
            reward = -100
            running = False

        total_reward += reward

        all_sprites.update()
        all_sprites.draw(screen)

        cv_image = detector.pygame_to_cvimage(screen)
        detector.collision(cv_image)
        state = get_state(detector)
        action = choose_action(state)

        if action == 2 and player.can_shoot():
            bullet = Bullet(player.rect.centerx, player.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            reward += 50
        else:
            player.update(True, action)

        next_state = get_state(detector)
        learn(state, action, reward, next_state)
        outline_image = detector.detect_shapes_in_image(cv_image)
        outline_image_swapped = np.swapaxes(outline_image, 0, 1)
        outline_surface = pygame.surfarray.make_surface(
            outline_image_swapped[:, :, ::-1])
        screen.blit(outline_surface, (0, 0))
        draw_text(f"Enemies Hit: {enemy_hits}", 10, 10)
        draw_text(f"All Time High Enemies Hit: {max_hits}", 10, 30)
        draw_text(f"Iterations: {iterations}", 10, 50)
        draw_text(f"AI Score (Total Reward): {total_reward}", 10, 70)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

        iterations += 1
        alpha *= alpha_decay
        epsilon *= epsilon_decay
    if max_hits < enemy_hits:
        max_hits = enemy_hits
    return game_over_screen(enemy_hits)


play_again = True
while play_again:
    play_again = main_game()

pygame.quit()
