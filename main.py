import pygame
import os
import random

pygame.init()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('cannot load image', fullname)
        raise SystemExit(message)

    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image.convert_alpha()
    return image


class button:
    def __init__(self, position, size, clr=[100, 100, 100], cngclr=None, func=None, text='',
                 font="Segoe Print", font_size=16, font_clr=[0, 0, 0]):
        self.clr  = clr
        self.size = size
        self.func = func
        self.surf = pygame.Surface(size)
        self.rect = self.surf.get_rect(center=position)

        if cngclr:
            self.cngclr = cngclr
        else:
            self.cngclr = clr

        if len(clr) == 4:
            self.surf.set_alpha(clr[3])

        self.font = pygame.font.SysFont(font, font_size)
        self.txt = text
        self.font_clr = font_clr
        self.txt_surf = self.font.render(self.txt, 1, self.font_clr)
        self.txt_rect = self.txt_surf.get_rect(center=[wh//2 for wh in self.size])

    def draw(self, screen):
        self.mouseover()

        self.surf.fill(self.curclr)
        self.surf.blit(self.txt_surf, self.txt_rect)
        screen.blit(self.surf, self.rect)

    def mouseover(self):
        self.curclr = self.clr
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.curclr = self.cngclr

    def isOver(self, pos):
        if pos[0] > self.rect.x and pos[0] < self.rect.x + self.size[0]:
            if pos[1] > self.rect.y and pos[1] < self.rect.y + self.size[1]:
                return True

        return False


class Tetris:
    # номера клеток в массиве 4 на 4 начиная с нуля
    figures = [[[1, 5, 9, 13], [4, 5, 6, 7]],
               [[1, 5, 8, 9], [1, 5, 6, 7], [1, 2, 5, 9], [1, 2, 3, 7]],
               [[1, 2, 4, 5], [0, 4, 5, 9]],
               [[0, 1, 5, 6], [1, 4, 5, 8]],
               [[1, 5, 9, 10], [1, 2, 3, 5], [1, 2, 6, 10], [2, 4, 5, 6]],
               [[0, 1, 2, 5], [1, 4, 5, 9], [1, 4, 5, 6], [1, 5, 6, 9]],
               [[1, 2, 5, 6]]]

    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.board = [[0] * width for _ in range(height)]
        self.active_figure = None
        self.is_game_active = False
        self.score = 0
        self.end = False
        self.is_record = False

        self.spawn_x = self.width // 2

        self.delete_row_sound = pygame.mixer.Sound(os.path.join('data', 'delete_row.wav'))

    def render(self, screen):
        for x in range(self.width):
            for y in range(self.height):
                pygame.draw.rect(screen, pygame.Color('grey'),
                                 (x * self.cell_size, y * self.cell_size,
                                  self.cell_size, self.cell_size), 1)
                if self.board[y][x] == 1:
                    pygame.draw.rect(screen, pygame.Color('red'),
                                     (x * self.cell_size, y * self.cell_size,
                                      self.cell_size, self.cell_size))
        if self.is_record:
            font = pygame.font.Font(None, 40)
            string_rendered = font.render(f"НОВЫЙ РЕКОРД", 1,
                                           pygame.Color(255, 211, 95))
            intro_rect = string_rendered.get_rect()
            intro_rect.y = self.height * self.cell_size // 2 + 50
            intro_rect.x = self.width * self.cell_size // 2 - 120
            screen.blit(string_rendered, intro_rect)

    def check_new_record(self):
        records = get_records()
        for i in range(len(records)):
            self.is_record = True
            if int(records[i]) < self.score:
                records = records[:i] + [str(self.score)] + records[i:-1]
                write_new_records(records)
                break
            self.is_record = False

    def new_figure(self):
        self.index_figure = random.randint(0, len(Tetris.figures) - 1)
        figure = Tetris.figures[self.index_figure][0]
        self.rotate = 0
        self.active_figure = []
        is_end = False
        for x in range(4):
            for y in range(4):
                if (y * 4) + x in figure and not is_end:
                    if self.board[y][x + self.spawn_x] != 1:
                        self.board[y][x + self.spawn_x] = 1
                        self.active_figure.append([x + self.spawn_x, y])
                    else:
                        self.check_new_record()
                        is_end = True
        if is_end:
            self.end = True

    def restart_game(self):
        self.end = False
        self.is_record = False
        self.board = [[0] * self.width for _ in range(self.height)]
        self.score = 0
        self.new_figure()

    def update(self):
        if self.check_space():
            for i in range(len(self.active_figure)):
                x, y = self.active_figure[i]
                self.board[y][x] = 0
                self.active_figure[i] = [x, y + 1]

            for i in self.active_figure:
                self.board[i[1]][i[0]] = 1
        else:
            self.active_figure = None

    def check_space(self):
        if all([i[1] != self.height - 1 for i in self.active_figure]) and \
                all([((self.board[i[1] + 1][i[0]] != 1) or ([i[0], i[1] + 1] in self.active_figure))
                     for i in self.active_figure]):
            return True
        else:
            return False

    def clear_figure(self):
        for i in self.active_figure:
            self.board[i[1]][i[0]] = 0

    def move(self, val):
        flag = False
        if val == -1:
            if self.active_figure:
                new_cord = []
                flag = True
                for i in self.active_figure:
                    if i[0] != 0 and (self.board[i[1]][i[0] - 1] != 1 or ([i[0] - 1, i[1]] in self.active_figure)):
                        new_cord.append([i[0] - 1, i[1]])
                    else:
                        flag = False
        elif val == 1:
            new_cord = []
            flag = True
            for i in self.active_figure:
                if i[0] != self.width - 1 and (self.board[i[1]][i[0] + 1] != 1 or (
                        [i[0] + 1, i[1]] in self.active_figure)):
                    new_cord.append([i[0] + 1, i[1]])
                else:
                    flag = False

        if flag:
            self.clear_figure()
            self.active_figure = new_cord
            for i in self.active_figure:
                self.board[i[1]][i[0]] = 1

    def check_full_row(self):
        for i in range(len(self.board)):
            flag = True
            for k in self.board[i]:
                if k != 1 or (self.active_figure and k in self.active_figure):
                    flag = False
                    break
            if flag:
                for k in range(self.width):
                    self.board[i][k] = 0
                for l in range(i, 0, -1):
                    for k in range(self.width):
                        if self.board[l - 1][k] == 1:
                            self.board[l][k] = 1
                            self.board[l - 1][k] = 0
                self.delete_row_sound.play()
                self.score += 100

    def rotate_figure(self):
        xd, yd = self.active_figure[0]
        last_rotate = self.rotate
        if self.rotate % 2 == 0:
            xd -= 1
        self.rotate = (self.rotate + 1) % len(Tetris.figures[self.index_figure])
        figure = Tetris.figures[self.index_figure][self.rotate]
        flag = True
        new = []
        for x in range(4):
            for y in range(4):
                if (y * 4) + x in figure:
                    new.append([x + xd, y + yd])
                    if x + xd >= self.width or y + yd >= self.height or\
                            (self.board[y+yd][x+xd] == 1 and
                             [x + xd, y + yd] not in self.active_figure):
                        flag = False

        if flag:
            self.clear_figure()
            self.active_figure = new
            for i in self.active_figure:
                self.board[i[1]][i[0]] = 1
        else:
            self.rotate = last_rotate

    def down_figure(self):
        while self.active_figure:
            self.score += 10
            self.update()


def start_btn():
    global menu_activ
    global game_activ
    global screen
    global size
    menu_activ = False
    game_activ = True
    screen = screen = pygame.display.set_mode(size)


def records_btn():
    global menu_activ
    global records_active

    menu_activ = False
    records_active = True


def exit_btn():
    global running
    global menu_activ
    running = False
    menu_activ = False


def back_to_menu():
    global screen
    global menu_activ
    global game_activ
    global records_active
    global menu_size

    menu_activ = True
    records_active = False
    game_activ = False
    screen = screen = pygame.display.set_mode(menu_size)


def get_records():
    fullname = os.path.join('data', 'records.txt')
    with open(fullname, 'r', encoding='utf8') as f:
        res = f.read().strip(';').split(';')
    return res


def write_new_records(records):
    fullname = os.path.join('data', 'records.txt')
    res = ';'.join(records)
    with open(fullname, 'w', encoding='utf8') as f:
        f.write(res)


def main():
    global running
    global menu_activ
    global game_activ
    global screen
    global size
    global records_active
    global menu_size
    cell_size = 20
    width_cells = 12
    height_cells = 20
    size = cell_size * width_cells, cell_size * height_cells + 30
    menu_size = (600, 500)
    screen = pygame.display.set_mode(menu_size)
    all_sprites = pygame.sprite.Group()
    clock = pygame.time.Clock()
    fps = 60
    running = True
    menu_activ = True
    records_active = False
    game_activ = False
    background = load_image('background.jpg')
    background = pygame.transform.scale(background, (menu_size))
    tetris = Tetris(width_cells, height_cells, cell_size)
    pygame.time.set_timer(pygame.USEREVENT, 200)

    button1 = button(position=(300, 150), size=(200, 50), clr=(220, 220, 220),
                     cngclr=(100, 100, 100), func=start_btn, text='START')
    button2 = button((300, 250), (200, 50), (220, 220, 220), (100, 100, 100), records_btn, 'RECORDS')
    button3 = button((300, 350), (200, 50), (220, 220, 220), (100, 100, 100), exit_btn, 'EXIT')

    button_list = [button1, button2, button3]

    back_to_menu_btn = button((60, 30), (100, 25), (220, 220, 220), (100, 100, 100), back_to_menu,
                             'BACK')

    pygame.mixer.music.load(os.path.join('data', 'theme.mp3'))
    pygame.mixer.music.set_volume(0.05)

    pygame.mixer.music.play(-1, 0, 5)

    while running:
        while menu_activ:
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    menu_activ = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for i in button_list:
                            if i.isOver(event.pos):
                                i.func()

            screen.blit(background, (0, 0))

            for b in button_list:
                b.draw(screen)

        while records_active:

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    records_active = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if back_to_menu_btn.isOver(event.pos):
                            back_to_menu_btn.func()

            records = get_records()
            font = pygame.font.Font(None, 60)
            screen.blit(background, (0, 0))
            back_to_menu_btn.draw(screen)
            text_coord = 50
            counter = 1
            for i in records:
                string_rendered = font.render(f"{str(counter)}: {i}", 1, pygame.Color(20, 15, 11))
                intro_rect = string_rendered.get_rect()
                text_coord += 10
                intro_rect.top = text_coord
                intro_rect.x = 200
                text_coord += intro_rect.height
                screen.blit(string_rendered, intro_rect)
                counter += 1

        while game_activ:
            if not tetris.end:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        game_activ = False

                    if not tetris.active_figure:
                        tetris.new_figure()

                    if event.type == pygame.USEREVENT:
                        tetris.update()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            tetris.move(-1)
                        if event.key == pygame.K_RIGHT:
                            tetris.move(1)
                        if event.key == pygame.K_UP:
                            tetris.rotate_figure()
                        if event.key == pygame.K_DOWN:
                            tetris.down_figure()

                font = pygame.font.Font(None, 20)
                string_rendered = font.render(f"SCORE: {tetris.score}", 1,
                                              pygame.Color(255, 255, 255))
                intro_rect = string_rendered.get_rect()
                intro_rect.y = tetris.height * tetris.cell_size + 10
                intro_rect.x = 10

                tetris.check_full_row()

            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        game_activ = False

                    if event.type == pygame.KEYDOWN:
                        tetris.restart_game()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if back_to_menu_btn.isOver(event.pos):
                            tetris.restart_game()
                            back_to_menu_btn.func()

                font = pygame.font.Font(None, 40)
                string_rendered = font.render(f"THE END", 1,
                                              pygame.Color(255, 211, 95))
                intro_rect = string_rendered.get_rect()
                intro_rect.y = tetris.height * tetris.cell_size // 2 - 50
                intro_rect.x = tetris.width * tetris.cell_size // 2 - 100

            screen.fill(pygame.Color('black'))
            tetris.render(screen)
            screen.blit(string_rendered, intro_rect)
            if tetris.end:
                font = pygame.font.Font(None, 40)
                string_rendered2 = font.render(f"SCORE: {tetris.score}", 1,
                                               pygame.Color(255, 211, 95))
                intro_rect2 = string_rendered.get_rect()
                intro_rect2.y = tetris.height * tetris.cell_size // 2
                intro_rect2.x = tetris.width * tetris.cell_size // 2 - 100
                screen.blit(string_rendered2, intro_rect2)
                back_to_menu_btn.draw(screen)
            all_sprites.draw(screen)
            pygame.display.flip()
            clock.tick(fps)

    pygame.quit()


if __name__ == '__main__':
    main()
