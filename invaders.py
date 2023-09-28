import numpy as np
import random
import pygame

from shapes import DetectShape
pygame.init()

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
detector = DetectShape()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

player_speed = 5
enemy_speed = 3

enemy_hits = 0
font = pygame.font.SysFont(None, 36)


def draw_text(text, x, y):
    """Utility function to draw text on the screen"""
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
        self.speed = -8  # Negative because it will move upwards

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
            if direction == True:
                self.rect.x += player_speed
            else:
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
    while waiting:
        exit()

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


def main_game():
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

    while running:
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
            running = False

        all_sprites.update()
        all_sprites.draw(screen)
        cv_image = detector.pygame_to_cvimage(screen)
        collision = detector.collision(cv_image)
        if collision is not None:
            print(collision)

        outline_image = detector.detect_shapes_in_image(cv_image)

        outline_image_swapped = np.swapaxes(outline_image, 0, 1)
        outline_surface = pygame.surfarray.make_surface(
            outline_image_swapped[:, :, ::-1])
        screen.blit(outline_surface, (0, 0))

        draw_text(f"Enemies Hit: {enemy_hits}", 10, 10)
        pygame.display.flip()
        pygame.time.Clock().tick(60)

    return game_over_screen(enemy_hits)


play_again = True
while play_again:
    play_again = main_game()

pygame.quit()
