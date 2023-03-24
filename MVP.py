import sys
import pycalculix as pyc
import cv2

IMAGE_PATH = r'C:\\Users\\Stepan\\Downloads\\0GtvVrB_Amw (1).jpg' # Путь к изображению будет отличаться

"""Часть, отвечающая за выделение контура"""
im = cv2.imread(IMAGE_PATH) # Читаем изображение с диска
im = im[700:1300, 250:2300] # Обрезаем нужную часть
imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) # Переводим в одноканальный формат
ret, threshold = cv2.threshold(imgray, 170, 255, 0) # Бинаризуем изображение в маску 1-0
contours, hierarhy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # Выделяем контур

"""Часть, отвечающая за создание и расчёт мат.модели"""
grav = 9.81 # m/s^2
X_LIMITS = [40, 140]
Y_LIMITS = [10, 610]


# Инициализация модели
proj_name = 'MVP'
model = pyc.FeaModel(proj_name, ccx = 'ccx_static.exe') #, ccx = r'cx_static.exe'
model.set_units('m') # this sets dist units to meters

# GUI интерфейс
show_gui = True
if '-nogui' in sys.argv:
    show_gui = False

# Задание формы элементов
eshape = 'quad'
if '-tri' in sys.argv:
    eshape = 'tri'

# Определение объекта геометрии мат.модели
part = pyc.Part(model)
# Внешний контур
out_lines = []
start_y, start_x = contours[16][0][0]
out_points = contours[16][1:]
part.goto(start_x*0.3048, start_y*0.3048)
for coords in out_points[::10]:
    y,x = coords[0]
    x,y = x*0.3048,y*0.3048 # conversion to metric
    [L1,p1,p2] = part.draw_line_to(x, y)
    out_lines.append([L1.points[0].x,L1.points[0].y,L1.points[1].x,L1.points[1].y])
L,q,w = part.draw_line_to(start_x*0.3048, start_y*0.3048)
out_lines.append([L.points[0].x,L.points[0].y,L.points[1].x,L.points[1].y])

# Внутренний контур
in_lines = []
start_y, start_x = contours[55][0][0]
in_points = contours[55][1:]
part.goto(start_x*0.3048, start_y*0.3048, holemode = True)
for coords in in_points[::10]:
    y,x = coords[0]
    x,y = x*0.3048, y*0.3048 # conversion to metric
    if (x > X_LIMITS[0]) and (x < X_LIMITS[1]) and (y > Y_LIMITS[0]) and (y < Y_LIMITS[1]):
        [L1,p1,p2] = part.draw_line_to(x, y)
        in_lines.append([L1.points[0].x,L1.points[0].y,L1.points[1].x,L1.points[1].y])
L,q,w = part.draw_line_to(start_x*0.3048, start_y*0.3048)
in_lines.append([L.points[0].x,L.points[0].y,L.points[1].x,L.points[1].y])

# Задаем нагрузки и ограничения
pressure = -1000
model.set_load('press', ['L8', 'L51'], pressure)
model.set_load('press', ['L54', 'L11'], pressure)
model.set_constr('fix', ['P60', 'P30'], 'y')
model.set_constr('fix', ['P24', 'P7'], 'x')

# Задаем материал изделия
mat = pyc.Material('steel')
mat.set_mech_props(7800, 210*(10**9), 0.3)
model.set_matl(mat, part)

# Задаем параметры построения сетки
model.set_eshape(eshape, 2)
model.set_etype('plstress', part, 0.1)
model.mesh(1.0, 'gmsh') # mesh 1.0 fineness, smaller is finer

model.plot_elements(proj_name+'_elem', display=show_gui)
model.plot_pressures(proj_name+'_press', display=show_gui)
model.plot_constraints(proj_name+'_constr', display=show_gui)

# Формируем объект решения
prob = pyc.Problem(model, 'struct')
prob.solve()

# Пост-обработка
"""
# view and query results
sx = prob.rfile.get_nmax('Sx')
print('Sx_max: %f' % sx)

# Plot results
# store the fields to plot
fields = 'Sx,Sy,S1,S2,S3,Seqv,ux,uy,utot,ex'
fields = fields.split(',')
for field in fields:
    fname = proj_name+'_'+field
    prob.rfile.nplot(field, fname, display=False)
"""
