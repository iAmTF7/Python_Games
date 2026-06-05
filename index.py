import pygame
import random
import math

pygame.init()

# ================= CONFIG =================

WIDTH = 1000
HEIGHT = 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soul Knight Style Improved")

clock = pygame.time.Clock()

# ================= COLORS =================

BLACK=(20,20,20)
WHITE=(230,230,230)

GREEN=(0,255,100)
RED=(255,70,70)
BLUE=(50,150,255)
YELLOW=(255,220,50)

GRAY=(80,80,80)
DARK=(40,40,40)

ROOM_COLORS=[

    (55,60,75),
    (70,50,80),
    (45,75,70),
    (80,55,55),
    (55,80,90),
    (75,65,45)
]
ROOM_BORDER=(90,100,120)

# ================= PLAYER =================

class Player:

    def __init__(self):

        self.x=WIDTH//2
        self.y=HEIGHT-120

        self.size=35

        # movement smooth
        self.speed=6
        self.vx=0
        self.vy=0

        self.accel=.7
        self.friction=.82

        self.max_hp=100
        self.hp=100

        self.max_armor=50
        self.armor=50

        self.max_energy=100
        self.energy=100

        self.damage=25

        self.level=1
        self.exp=0
        self.exp_need=100
    

        self.hp_regen=0
        self.armor_regen=0
        self.energy_regen=0

        self.special_items=[]
    
    def move(self,keys):

        if keys[pygame.K_w]:
            self.vy-=self.accel

        if keys[pygame.K_s]:
            self.vy+=self.accel

        if keys[pygame.K_a]:
            self.vx-=self.accel

        if keys[pygame.K_d]:
            self.vx+=self.accel

        self.vx*=self.friction
        self.vy*=self.friction

        self.vx=max(-self.speed,min(self.speed,self.vx))
        self.vy=max(-self.speed,min(self.speed,self.vy))

        self.x+=self.vx
        self.y+=self.vy

        self.x=max(60,min(WIDTH-60,self.x))
        self.y=max(10,min(HEIGHT-60,self.y))

    def draw(self):

        pygame.draw.rect(
            screen,
            GREEN,
            (self.x,self.y,self.size,self.size),
            border_radius=8
        )
    def add_exp(self,amount):
        self.exp+=amount
        while self.exp>=self.exp_need:
            self.exp-=self.exp_need
            self.level+=1
            self.exp_need=int(
                self.exp_need*1.3
            )
            self.max_hp+=10
            self.max_armor+=5
            self.damage+=3
            self.hp=self.max_hp
            self.armor=self.max_armor
    
# ================= BULLET =================

class Bullet:

    def __init__(self,x,y,mx,my,damage):

        self.x=x
        self.y=y

        self.damage=damage
        self.speed=13
        self.size=5

        dx=mx-x
        dy=my-y

        dist=math.hypot(dx,dy)

        if dist==0:
            dist=1

        self.dx=dx/dist*self.speed
        self.dy=dy/dist*self.speed

    def move(self):

        self.x+=self.dx
        self.y+=self.dy

    def draw(self):

        pygame.draw.circle(
            screen,
            YELLOW,
            (int(self.x),int(self.y)),
            self.size
        )

    def outside(self):

        return(
            self.x<0 or
            self.x>WIDTH or
            self.y<0 or
            self.y>HEIGHT
        )


# ================= ENEMY =================

class Enemy:

    def __init__(self,level):

        self.size=30

        self.x=random.randint(
            100,
            WIDTH-100
        )

        self.y=random.randint(
            100,
            HEIGHT-250
        )

        self.speed=random.uniform(
            1.5,
            2.5
        )

        self.max_hp=40+level*10
        self.hp=self.max_hp

    def move(self,player):

        dx=player.x-self.x
        dy=player.y-self.y

        dist=math.hypot(dx,dy)

        if dist==0:
            dist=1

        self.x+=dx/dist*self.speed
        self.y+=dy/dist*self.speed

    def attack(self,player):

        dist=math.hypot(
            player.x-self.x,
            player.y-self.y
        )

        if dist<35:

            if player.armor>0:

                player.armor=max(
                    0,
                    player.armor-.25
                )

            else:

                player.hp=max(
                    0,
                    player.hp-.25
                )

    def draw(self):

        pygame.draw.rect(
            screen,
            RED,
            (self.x,self.y,self.size,self.size),
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            GRAY,
            (self.x,self.y-10,self.size,5)
        )

        hp=(self.hp/self.max_hp)*self.size

        pygame.draw.rect(
            screen,
            GREEN,
            (self.x,self.y-10,hp,5)
        )


# ================= ITEM =================

class Item:

    def __init__(self,x,y,player):

        self.x=x
        self.y=y
        self.size=20

        special_types=[

            "regen_hp",
            "regen_armor",
            "regen_energy"
        ]

        owned=player.special_items.copy()

        roll=random.random()

        # 2%

        if roll<0.02:

            possible=[]

            for t in special_types:
                if t not in owned:
                    possible.append(t)

            if len(possible)>0:

                self.type=random.choice(
                    possible
                )

            else:

                self.type=random.choice(
                    ["heal","armor","energy"]
                )

        else:

            r=random.random()

            if r<0.34:
                self.type="heal"

            elif r<0.67:
                self.type="armor"

            else:
                self.type="energy"

        self.colors={

            "heal":(0,255,100),
            "armor":(50,150,255),
            "energy":(0,255,255),

            "regen_hp":(255,0,255),
            "regen_armor":(255,140,0),
            "regen_energy":(255,255,120)
        }

    def draw(self):

        pygame.draw.circle(
            screen,
            self.colors[self.type],
            (self.x+10,self.y+10),
            10
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (self.x+10,self.y+10),
            10,
            2
        )


# ================= ROOM =================

class Room:

    last_color=None

    def __init__(self,level):

        self.level=level

        self.enemies=[]
        self.items=[]

        self.cleared=False
        colors=ROOM_COLORS.copy()

        if Room.last_color in colors:
            colors.remove(
                Room.last_color
            )

        self.bg=random.choice(
            colors
        )

        Room.last_color=self.bg

        amount=random.randint(
            3+level,
            5+level
        )

        for i in range(amount):

            self.enemies.append(
                Enemy(level)
            )

    def update(self,player):

        for enemy in self.enemies:

            enemy.move(player)
            enemy.attack(player)

        if len(self.enemies)==0:
            self.cleared=True

    def drop_item(self,x,y,player):

        # drop cân bằng ~40%

        if random.random()<0.4:

            self.items.append(
                Item(
                    x,
                    y,
                    player
                )
            )

    def draw(self):

        pygame.draw.rect(

            screen,
            self.bg,

            (
                50,
                50,
                WIDTH-100,
                HEIGHT-100
            ),

            border_radius=12
        )

        pygame.draw.rect(

            screen,
            ROOM_BORDER,

            (
                50,
                50,
                WIDTH-100,
                HEIGHT-100
            ),

            4,
            border_radius=12
        )

        pygame.draw.rect(screen,BLACK,(0,0,WIDTH,50))
        pygame.draw.rect(screen,BLACK,(0,HEIGHT-50,WIDTH,50))
        pygame.draw.rect(screen,BLACK,(0,0,50,HEIGHT))
        pygame.draw.rect(screen,BLACK,(WIDTH-50,0,50,HEIGHT))

        if self.cleared:

            pygame.draw.rect(

                screen,
                BLUE,

                (
                    WIDTH//2-50,
                    0,
                    100,
                    50
                )
            )

        for enemy in self.enemies:
            enemy.draw()

        for item in self.items:
            item.draw()


# ================= GAME =================

class Game:

    def __init__(self):

        self.player=Player()
        self.room=Room(1)

        self.bullets=[]

        self.running=True

        self.font=pygame.font.SysFont(
            None,
            30
        )

    def event(self):

        for event in pygame.event.get():

            if event.type==pygame.QUIT:

                self.running=False

            if event.type==pygame.MOUSEBUTTONDOWN:

                if self.player.energy>=2:

                    mx,my=pygame.mouse.get_pos()

                    self.bullets.append(

                        Bullet(
                            self.player.x+15,
                            self.player.y+15,
                            mx,
                            my,
                            self.player.damage
                        )
                    )

                    self.player.energy-=2
    def pickup(self):

        for item in self.room.items[:]:

            dist=math.hypot(

                (self.player.x+self.player.size/2)-
                (item.x+item.size/2),

                (self.player.y+self.player.size/2)-
                (item.y+item.size/2)
            )

            if dist<25:

                if item.type=="heal":

                    self.player.hp=min(
                        self.player.hp+20,
                        self.player.max_hp
                    )

                elif item.type=="armor":

                    self.player.armor=min(
                        self.player.armor+20,
                        self.player.max_armor
                    )

                elif item.type=="energy":

                    self.player.energy=min(
                        self.player.energy+30,
                        self.player.max_energy
                    )

                elif item.type=="regen_hp":

                    if item.type not in self.player.special_items:

                        self.player.hp_regen=.2
                        self.player.special_items.append(
                            item.type
                        )

                elif item.type=="regen_armor":

                    if item.type not in self.player.special_items:

                        self.player.armor_regen=.2
                        self.player.special_items.append(
                            item.type
                        )

                elif item.type=="regen_energy":

                    if item.type not in self.player.special_items:

                        self.player.energy_regen=.25
                        self.player.special_items.append(
                            item.type
                        )

                # luôn xóa item sau khi nhặt
                self.room.items.remove(item)

    def update(self):

        keys=pygame.key.get_pressed()

        self.player.move(keys)

        self.room.update(self.player)

        self.player.hp=min(
            self.player.hp+self.player.hp_regen,
            self.player.max_hp
        )

        self.player.armor=min(
            self.player.armor+self.player.armor_regen,
            self.player.max_armor
        )

        self.player.energy=min(
            self.player.energy+self.player.energy_regen,
            self.player.max_energy
        )


        # xử lý đạn
        for bullet in self.bullets[:]:

            bullet.move()

            if bullet.outside():

                self.bullets.remove(bullet)
                continue


            for enemy in self.room.enemies[:]:

                hit=(

                    enemy.x<bullet.x<enemy.x+enemy.size
                    and
                    enemy.y<bullet.y<enemy.y+enemy.size

                )

                if hit:

                    enemy.hp-=bullet.damage

                    if bullet in self.bullets:
                        self.bullets.remove(
                            bullet
                        )

                    if enemy.hp<=0:

                        self.player.add_exp(25)

                        self.room.drop_item(
                            enemy.x,
                            enemy.y,
                            self.player
                        )

                        self.room.enemies.remove(
                            enemy
                        )

                    break


        # cập nhật trạng thái phòng
        self.room.cleared=(
            len(self.room.enemies)==0
        )


        # chuyển phòng
        if self.room.cleared:

            player_center_x=(

                self.player.x+
                self.player.size/2

            )

            in_door=(

                WIDTH//2-50
                <=player_center_x<=
                WIDTH//2+50

            )

            if self.player.y<=50 and in_door:

                self.room=Room(
                    self.player.level
                )

                self.player.x=WIDTH//2
                self.player.y=HEIGHT-120

            self.pickup()

    def draw_ui(self):

        pygame.draw.rect(
            screen,
            DARK,
            (10,10,260,120),
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                20,
                20,
                self.player.hp/
                self.player.max_hp*220,
                20
            )
        )

        pygame.draw.rect(
            screen,
            BLUE,
            (
                20,
                50,
                self.player.armor/
                self.player.max_armor*220,
                15
            )
        )

        pygame.draw.rect(
            screen,
            YELLOW,
            (
                20,
                75,
                self.player.energy/
                self.player.max_energy*220,
                12
            )
        )

    def draw(self):

        screen.fill(BLACK)

        self.room.draw()

        self.player.draw()

        for bullet in self.bullets:
            bullet.draw()

        self.draw_ui()

        pygame.display.update()

    def run(self):

        while self.running:

            clock.tick(FPS)

            self.event()

            self.update()

            self.draw()
            txt=self.font.render(
                f"LV:{self.player.level}",
                True,
                WHITE
                )
            screen.blit(
                txt,
                (20,100)
                )
            pygame.draw.rect(
                screen,
                GRAY,
                (20,130,220,10)
                )
            pygame.draw.rect(
                screen,
                GREEN,
                (
                    20,
                    130,
                    self.player.exp/
                    self.player.exp_need*220,
                    10
                )
            )


if __name__ == "__main__":
    game=Game()
    game.run()

pygame.quit()