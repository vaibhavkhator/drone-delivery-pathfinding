import pygame
import heapq
import math
import time

pygame.init()

# Constants
WIDTH, HEIGHT = 400, 450
GRID_SIZE = 40
FPS = 60
WHITE = (255, 255, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
BLUE = (100, 100, 255)
BLACK = (30, 30, 30)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 150)
DARK_GRAY = (50, 50, 50)
DARK_LINE = (20, 20, 20)
PURPLE = (147, 112, 219)

# Grid dimensions
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = (HEIGHT - 150) // GRID_SIZE

# Game state
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drone Delivery Pathfinding")
clock = pygame.time.Clock()

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.parent = None
        self.is_obstacle = False

    def __lt__(self, other):
        return self.f < other.f

# Grid initialization
grid = [[Node(x, y) for y in range(GRID_HEIGHT)] for x in range(GRID_WIDTH)]
start, end = None, None
obstacles = set()
path = []
drone_pos = None
selected_tool = None
running = False
drone_moving = False
status_message = ""
completed_path = []
pulse_timer = 0
completion_animation = False
animation_timer = 0

# Button definitions
buttons = [
    {"text": "Start", "rect": pygame.Rect(20, HEIGHT-120, 80, 40), "color": GREEN, "hover": (150, 255, 150)},
    {"text": "End", "rect": pygame.Rect(110, HEIGHT-120, 80, 40), "color": RED, "hover": (255, 150, 150)},
    {"text": "Obstacle", "rect": pygame.Rect(200, HEIGHT-120, 80, 40), "color": BLACK, "hover": (80, 80, 80)},
    {"text": "Run", "rect": pygame.Rect(290, HEIGHT-120, 80, 40), "color": BLUE, "hover": (150, 150, 255)},
    {"text": "Reset", "rect": pygame.Rect(20, HEIGHT-60, 80, 40), "color": GRAY, "hover": (230, 230, 230)}
]

def draw_grid():
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, DARK_LINE, rect, 1)

            node = grid[x][y]
            if node.is_obstacle:
                pygame.draw.rect(screen, BLACK, rect)

            if (x, y) == start:
                pygame.draw.rect(screen, GREEN, rect)
            elif (x, y) == end:
                pygame.draw.rect(screen, RED, rect)
            elif (x, y) in path:
                pygame.draw.rect(screen, YELLOW, rect)
            elif completion_animation and (x, y) in completed_path:
                color = (min(255, 200 + int(55 * math.sin(pulse_timer))), 255, 200)
                pygame.draw.rect(screen, color, rect)

    if drone_pos:
        pygame.draw.circle(screen, PURPLE, (drone_pos[0] * GRID_SIZE + GRID_SIZE//2, drone_pos[1] * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//3)

def draw_buttons():
    for btn in buttons:
        color = btn["hover"] if btn["rect"].collidepoint(pygame.mouse.get_pos()) else btn["color"]
        pygame.draw.rect(screen, color, btn["rect"])
        pygame.draw.rect(screen, DARK_GRAY, btn["rect"], 2)
        text = pygame.font.SysFont(None, 24).render(btn["text"], True, DARK_GRAY)
        screen.blit(text, (btn["rect"].x + (btn["rect"].width - text.get_width()) // 2, btn["rect"].y + (btn["rect"].height - text.get_height()) // 2))

def neighbors(node):
    dirs = [(0,1),(1,0),(0,-1),(-1,0)]
    result = []
    for dx, dy in dirs:
        nx, ny = node.x + dx, node.y + dy
        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and not grid[nx][ny].is_obstacle:
            result.append(grid[nx][ny])
    return result

def heuristic(a, b):
    return abs(a.x - b.x) + abs(a.y - b.y)

def a_star(start_node, end_node):
    for row in grid:
        for node in row:
            node.g = float('inf')
            node.f = float('inf')
            node.parent = None

    open_set = []
    start_node.g = 0
    start_node.f = heuristic(start_node, end_node)
    heapq.heappush(open_set, start_node)

    while open_set:
        current = heapq.heappop(open_set)

        if current == end_node:
            path = []
            while current:
                path.append((current.x, current.y))
                current = current.parent
            return path[::-1]

        for neighbor in neighbors(current):
            tentative_g = current.g + 1
            if tentative_g < neighbor.g:
                neighbor.parent = current
                neighbor.g = tentative_g
                neighbor.f = tentative_g + heuristic(neighbor, end_node)
                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)
    return []

def handle_click(pos):
    global start, end, selected_tool
    grid_x, grid_y = pos[0] // GRID_SIZE, pos[1] // GRID_SIZE
    if grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
        return

    if selected_tool == "Start":
        start = (grid_x, grid_y)
    elif selected_tool == "End":
        end = (grid_x, grid_y)
    elif selected_tool == "Obstacle":
        grid[grid_x][grid_y].is_obstacle = not grid[grid_x][grid_y].is_obstacle

def handle_buttons(pos):
    global selected_tool, running, path, drone_pos, drone_moving, completed_path, completion_animation
    for btn in buttons:
        if btn["rect"].collidepoint(pos):
            if btn["text"] in ["Start", "End", "Obstacle"]:
                selected_tool = btn["text"]
            elif btn["text"] == "Run":
                if start and end:
                    path.clear()
                    completed_path.clear()
                    result = a_star(grid[start[0]][start[1]], grid[end[0]][end[1]])
                    if result:
                        path.extend(result)
                        drone_pos = start
                        drone_moving = True
                        completion_animation = False
            elif btn["text"] == "Reset":
                reset_grid()

def reset_grid():
    global start, end, obstacles, path, drone_pos, running, drone_moving, completed_path, completion_animation
    start = end = None
    for row in grid:
        for node in row:
            node.is_obstacle = False
    path.clear()
    completed_path.clear()
    drone_pos = None
    running = False
    drone_moving = False
    completion_animation = False

def main():
    global drone_pos, drone_moving, completed_path, pulse_timer, completion_animation, animation_timer

    running = True
    while running:
        screen.fill(WHITE)
        draw_grid()
        draw_buttons()

        if drone_moving and path:
            time.sleep(0.1)
            drone_pos = path.pop(0)
            completed_path.append(drone_pos)
            if not path:
                drone_moving = False
                completion_animation = True
                animation_timer = pygame.time.get_ticks()

        if completion_animation:
            pulse_timer += 0.1
            if pygame.time.get_ticks() - animation_timer > 3000:
                completion_animation = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[1] < HEIGHT - 150:
                    handle_click(event.pos)
                else:
                    handle_buttons(event.pos)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
