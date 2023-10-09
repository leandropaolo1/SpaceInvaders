import numpy as np
import random
import pygame
import pickle

from shapes import DetectShape

pygame.init()

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
detector = DetectShape()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

player_speed = 10
enemy_speed = 10

font = pygame.font.SysFont(None, 36)


def draw_text(text, x, y):
    rendeGRAY = font.render(text, True, GRAY)
    screen.blit(rendeGRAY, (x, y))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([10, 10], pygame.SRCALPHA)
        pygame.draw.circle(self.image, GRAY, (5, 5), 5)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = -8

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
            if direction == -1 and self.rect.left > 0:
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


def game_over_screen(enemy_hits):
    screen.fill(WHITE)
    draw_text("GAME OVER", WIDTH // 2 - 100, HEIGHT // 2 - 40)
    draw_text(f"Score: {enemy_hits}", WIDTH // 2 - 70, HEIGHT // 2)
    draw_text("Press R to play again or Q to quit",
              WIDTH // 2 - 220, HEIGHT // 2 + 40)

    pygame.display.flip()

    waiting = True
    return True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Play again
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()


Q = {}
alpha = 0.1
gamma = 0.9
epsilon = 0.1
alpha_decay = 0.999
epsilon_decay = 0.9995
EDGE_THRESHOLD = 50


def save_q_values():
    with open("q_values.pkl", "wb") as f:
        pickle.dump(Q, f)


def load_q_values():
    global Q
    try:
        with open("q_values.pkl", "rb") as f:
            Q = pickle.load(f)
    except FileNotFoundError:
        pass


def get_state(detector):
    enemies_pos = detector.rectangle_positions
    player_pos = detector.triangle_position

    if not enemies_pos or not player_pos:
        return None

    player_x = player_pos[2][0]
    player_top = player_pos[2][1]  # Tip of the triangle
    player_bottom = player_pos[0][1]  # Base of the triangle
    close_to_left_edge = player_x <= EDGE_THRESHOLD
    close_to_right_edge = player_x >= (WIDTH - EDGE_THRESHOLD)

    # Get the closest enemy that will collide with any part of the player's triangle
    colliding_enemies = [pos for pos in enemies_pos if pos[1]
                         >= player_top and pos[1] <= player_bottom]
    if colliding_enemies:
        closest_enemy = min(colliding_enemies, key=lambda pos: pos[1])
    else:
        closest_enemy = min(enemies_pos, key=lambda pos: pos[1])

    return (player_x, closest_enemy[0], closest_enemy[1], close_to_left_edge, close_to_right_edge)


def choose_action(state):
    if not state:
        return random.choice([-1, 1])
    if state[2]:  # close_to_left_edge
        valid_actions = [0, 1]
        Q[state][0] = -1e5
    elif state[3]:  # close_to_right_edge
        valid_actions = [-1, 0]
        Q[state][2] = -1e5
    else:
        valid_actions = [-1, 0, 1]

    if random.uniform(0, 1) < epsilon:
        return random.choice(valid_actions)
    else:
        q_values = Q.get(state, [random.uniform(-1, 1) for _ in range(3)])
        action_idx = np.argmax(
            [q_values[i+1] if i in valid_actions else -np.inf for i in [-1, 0, 1]])
        return [-1, 0, 1][action_idx]


def learn(state, action, reward, next_state):
    current_q = Q.get(state, [random.uniform(-1, 1)
                      for _ in range(3)])[action + 1]
    max_next_q = max(
        Q.get(next_state, [random.uniform(-1, 1) for _ in range(3)]))
    new_q = current_q + alpha * (reward + gamma * max_next_q - current_q)
    if state not in Q:
        Q[state] = [random.uniform(-1, 1) for _ in range(3)]
    Q[state][action + 1] = new_q


episode_hits = []
iterations = 0


def main_game():
    global iterations, alpha, epsilon
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    enemies = pygame.sprite.Group()
    for i in range(5):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    running = True
    enemy_hits = 0
    total_reward = 0
    last_action = None
    last_state = None

    while running:
        reward = 100  # Reward for avoidance

        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    all_sprites.add(bullet)
                    bullets.add(bullet)

        hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
        for hit in hits:
            enemy_hits += 1
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
        state = get_state(detector)

        if state:
            action = choose_action(state)
            player.update(True, action)
        else:
            action = random.choice([-1, 1])
            player.update(True, action)

        next_state = get_state(detector)

        if last_state is not None and last_action is not None:
            learn(last_state, last_action, reward, next_state)

        last_state = state
        last_action = action

        outline_image = detector.detect_shapes_in_image(cv_image)
        outline_image_swapped = np.swapaxes(outline_image, 0, 1)
        outline_surface = pygame.surfarray.make_surface(
            outline_image_swapped[:, :, ::-1])
        screen.blit(outline_surface, (0, 0))
        draw_text(f"Enemies Hit: {enemy_hits}", 10, 10)
        draw_text(f"Iterations: {iterations}", 10, 30)
        draw_text(f"AI Score (Total Reward): {total_reward}", 10, 50)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

        iterations += 1  # increment iterations

        # Decay the learning rate and exploration rate
        alpha *= alpha_decay
        epsilon *= epsilon_decay

    return game_over_screen(enemy_hits)


load_q_values()  # Load the Q-values at the start
play_again = True
while play_again:
    play_again = main_game()

save_q_values()  # Save the Q-values at the end
with open("episode_hits.txt", "w") as f:
    for hits in episode_hits:
        f.write(f"{hits}\n")

pygame.quit()
