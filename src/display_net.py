import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
from tqdm import tqdm
from PIL import Image
import pygame
import numpy as np
import math
import networkx as nx
from scipy.spatial.transform import Rotation
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA
from temp_settings import *

FPS = 60

WINDOW_SIZE = 625
MARGIN_SIZE = 15
BUTTON_SIZE = 16

SENSITIVITY = 0.4
DAMPING_FACTOR = 0.97

# DIMENSIONS = 3
# ITERATIONS = 500

WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BLACK = (0, 0, 0)

CHARACTERS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CHAR_TO_VALUE = {char: index for index, char in enumerate(CHARACTERS)}

def base62_to_int(b62_str):
    return sum(CHAR_TO_VALUE[char]*(62**i) for i, char in enumerate(reversed(b62_str)))

HUE_WHEEL = Image.open('assets/hue_wheel.png')
hue_width = HUE_WHEEL.size[0]

def get_hue_colors(num_colors, offset=0):
    return [
        np.array(HUE_WHEEL.getpixel((round(offset + (hue_width-1) * i/num_colors) % (hue_width-1), 0))).astype(np.uint8)
        for i in range(num_colors)
    ]
def generate_label_colors(nodes, label_colors):
    return [
        label_colors[base62_to_int(str(node).split('.')[1])] if '.' in str(node) else label_colors[0]
        for node in nodes
    ]

def read_net_file(file_path):
    return nx.read_pajek(file_path)

def apply_spring_layout_nd(G, iterations=300, k=None):
    if k is None:
        k = 1 / math.pow(len(G.nodes()), 1/DIMENSIONS)

    pos = {node: np.random.rand(DIMENSIONS) for node in G.nodes()}
    nodes = list(G.nodes())
    t = 0.1
    dt = t / float(iterations+1)

    for _ in tqdm(range(iterations)):
        disp = {node: np.zeros(DIMENSIONS) for node in G.nodes()}
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1:]:
                delta = pos[node1] - pos[node2]
                dist = np.linalg.norm(delta)
                if dist != 0:
                    factor = k * k / dist
                    disp[node1] += delta/dist*factor
                    disp[node2] -= delta/dist*factor

        for edge in G.edges():
            delta = pos[edge[0]] - pos[edge[1]]
            dist = np.linalg.norm(delta)
            if dist != 0:
                factor = dist * dist / k
                disp[edge[0]] -= delta/dist*factor
                disp[edge[1]] += delta/dist*factor

        for node in G.nodes():
            dist = np.linalg.norm(disp[node])
            if dist != 0:
                pos[node] += disp[node]/dist*min(dist, t)
        t -= dt

    return np.array([pos[node] for node in G.nodes()])

def normalize_positions(positions):
    if DIMENSIONS == 2:
        positions = np.hstack((positions, np.zeros((len(positions), 1))))
    elif DIMENSIONS == 3:
        pca = PCA(n_components=3)
        pca.fit(positions)
        positions = pca.transform(positions)
    elif DIMENSIONS > 3:
        pca = PCA(n_components=3)
        positions = pca.fit_transform(positions)
    
    distances = pdist(positions)
    max_distance = np.max(distances)

    indices = np.triu_indices(len(positions), k=1)
    threshold = max_distance * 0.05
    close_to_max = (distances >= max_distance-threshold) & (distances <= max_distance+threshold)
    i_indices, j_indices = indices[0][close_to_max], indices[1][close_to_max]
    
    midpoints = [(positions[i] + positions[j])/2 for i, j in zip(i_indices, j_indices)]
    if midpoints:
        center = np.mean(midpoints, axis=0)
    else:
        center = np.mean(positions, axis=0)
    
    centered_positions = positions - center
    
    max_distance_from_center = np.max(np.linalg.norm(centered_positions, axis=1))
    scale_factor = (WINDOW_SIZE - 2*MARGIN_SIZE) / (2*max_distance_from_center)
    normalized = centered_positions * scale_factor
    normalized += WINDOW_SIZE/2
    return normalized

def prepare_graph(file_path):
    G = read_net_file(file_path)
    
    print(f'total number of vertices: {G.number_of_nodes()}')
    print(f'total number of edges: {G.number_of_edges()}')
    
    if nx.is_directed(G):
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    
    num_components = len(components)
    print(f'number of disconnected graphs: {num_components}')
    
    if num_components == 0:
        raise ValueError('no components found.')
    
    subgraphs = [G.subgraph(c).copy() for c in components]
    subgraphs = [sg for sg in subgraphs if sg.number_of_nodes() >= 3]
    subgraphs = sorted(subgraphs, key=lambda sg: sg.number_of_nodes(), reverse=True)
    
    positioned_subgraphs = []
    for sg in subgraphs:
        positions = apply_spring_layout_nd(sg, ITERATIONS)
        normalized_positions = normalize_positions(positions)
        positioned_subgraphs.append((sg, normalized_positions))
    
    return positioned_subgraphs

def draw_graph(screen, font, G, positions, rotation_quat, colors):
    screen.fill(BLACK)
    rotated_positions = rotation_quat.apply(positions - WINDOW_SIZE/2) + WINDOW_SIZE/2
    
    for edge in G.edges():
        start = rotated_positions[list(G.nodes()).index(edge[0])][:2]
        end = rotated_positions[list(G.nodes()).index(edge[1])][:2]
        pygame.draw.line(screen, (128, 128, 128), start, end)
    
    for i, node in enumerate(G.nodes()):
        pos = rotated_positions[i][:2]
        label = str(node)
        color = colors[i]
        text_surface = font.render(label, False, color)
        text_rect = text_surface.get_rect(center=pos)
        
        bg_rect = pygame.Rect(text_rect.left-1, text_rect.top+3,
                              text_rect.width+2, text_rect.height-4)
        pygame.draw.rect(screen, BLACK, bg_rect)
        
        screen.blit(text_surface, text_rect)

def draw_selection_panel(screen, font, current_index, total_components):
    left_arrow = pygame.Rect(0, 0, BUTTON_SIZE, BUTTON_SIZE)
    right_arrow = pygame.Rect(BUTTON_SIZE, 0, BUTTON_SIZE, BUTTON_SIZE)
    reset_button = pygame.Rect(WINDOW_SIZE - BUTTON_SIZE, 0, BUTTON_SIZE, BUTTON_SIZE)
    pygame.draw.rect(screen, DARK_GRAY, left_arrow)
    pygame.draw.rect(screen, DARK_GRAY, right_arrow)
    pygame.draw.rect(screen, DARK_GRAY, reset_button)
    
    left_text = font.render('<', False, WHITE)
    left_text_rect = left_text.get_rect(centerx=left_arrow.centerx-1, centery=left_arrow.centery-1)
    screen.blit(left_text, left_text_rect)
    
    right_text = font.render('>', False, WHITE)
    right_text_rect = right_text.get_rect(centerx=right_arrow.centerx, centery=right_arrow.centery-1)
    screen.blit(right_text, right_text_rect)
    
    reset_text = font.render('R', False, WHITE)
    reset_text_rect = reset_text.get_rect(centerx=reset_button.centerx, centery=reset_button.centery-1)
    screen.blit(reset_text, reset_text_rect)
    
    text = f' {current_index+1} of {total_components}'
    text_surface = font.render(text, False, WHITE)
    text_rect = text_surface.get_rect(left=right_arrow.right, centery=right_arrow.centery-1)
    screen.blit(text_surface, text_rect)

def main():
    file_path = 'graph.net'
    with open(file_path, 'r') as file:
        first_line = file.readline().strip()
        EDO = int(first_line[1:])
    label_colors = get_hue_colors(EDO, 145)

    try:
        positioned_subgraphs = prepare_graph(file_path)
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)
    
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption('chord transformation viewer')
    pygame.display.set_icon(pygame.image.load('assets/icon.png'))
    font = pygame.font.Font('assets/JetBrainsMono-Regular.otf', 12)
    clock = pygame.time.Clock()

    rotation_quat = Rotation.from_quat([0, 0, 0, 1])
    angular_velocity = np.zeros(3)
    last_pos = None
    current_component = 0
    running = True

    G, positions = positioned_subgraphs[current_component]
    colors = generate_label_colors(G, label_colors)

    SCREEN_CENTER = np.array([WINDOW_SIZE/2, WINDOW_SIZE/2, 0])
    ROTATION_SCALE = SENSITIVITY*85 / WINDOW_SIZE
    sensitivity = SENSITIVITY/WINDOW_SIZE
        
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = event.pos
                    y_col = y < BUTTON_SIZE
                    if (0 <= x < BUTTON_SIZE) and y_col:
                        current_component = (current_component - 1) % len(positioned_subgraphs)
                        G, positions = positioned_subgraphs[current_component]
                        colors = generate_label_colors(G, label_colors)
                    elif (BUTTON_SIZE <= x < 2 * BUTTON_SIZE) and y_col:
                        current_component = (current_component + 1) % len(positioned_subgraphs)
                        G, positions = positioned_subgraphs[current_component]
                        colors = generate_label_colors(G, label_colors)
                    elif (WINDOW_SIZE - BUTTON_SIZE <= x < WINDOW_SIZE) and y_col:
                        rotation_quat = Rotation.from_quat([0, 0, 0, 1])
                        angular_velocity = np.zeros(3)
                    else:
                        last_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    last_pos = None
            elif event.type == pygame.MOUSEMOTION and last_pos is not None:
                x, y = event.pos
                dx = x - last_pos[0]
                dy = y - last_pos[1]
                
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LCTRL] or keys[pygame.K_LSHIFT] or DIMENSIONS == 2:
                    mouse_vec = np.array([x, y, 0]) - SCREEN_CENTER
                    mouse_vec_prev = np.array([last_pos[0], last_pos[1], 0]) - SCREEN_CENTER
                    
                    cross_product = np.cross(mouse_vec_prev, mouse_vec)
                    dot_product = np.dot(mouse_vec_prev, mouse_vec)
                    angle = np.arctan2(np.linalg.norm(cross_product), dot_product)
                    
                    angular_velocity[2] -= np.copysign(angle * ROTATION_SCALE, -cross_product[2])
                else:
                    angular_velocity[1] += dx * sensitivity
                    angular_velocity[0] -= dy * sensitivity

                last_pos = (x, y)

        angle = np.linalg.norm(angular_velocity)
        if angle > 0:
            axis = angular_velocity / angle
            rot_delta = Rotation.from_rotvec(angle * axis)
            rotation_quat = rot_delta * rotation_quat

        angular_velocity *= DAMPING_FACTOR

        draw_graph(screen, font, G, positions, rotation_quat, colors)
        draw_selection_panel(screen, font, current_component, len(positioned_subgraphs))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()