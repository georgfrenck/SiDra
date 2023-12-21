
from tkinter import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
import math
import os

import faulthandler
faulthandler.enable()

class Paint(object):
    points = []
    lines = []
    triangles = []
    A12 = []
    A01 = []
    marked_line = None
    marked_triangle = None
    marked_point3d = None
    marked_point = None
    marked_point2 = None
    distance = None
    Basepoint = None
    Datafile = None

    def __init__(self):
        # init for gui. Gui has one toplevel (root) with 3 panels on the left side, one for points, one for lines and
        # one for triangles. Each panel has a listbox with a corresponding scrollbar and one Button to add new Data
        # on the bottom left there is a button to delete selected items of the listboxes.
        # in the top row there are the different buttons. One button to read in new data, one to erase all the data and
        # clear the canvas, three buttons to draw 0/1/2 simplices, one button to use the eraser in 2d mode.
        # There is also a slider to rotate the 3d image, which is useless in the 2d mode and 2 checkboxes to display
        # the triangles and the point numbers.
        # In the middle there is the canvas where the image is drawn and on the right next to it there are two
        # figures to display the chain complex and the homology of it. In the bottom right corner there is a button
        # to save all the current data as a textfile in the /Data folder
        self.Lb1 = None
        self.root = Tk()

        self.var_show_triangles = IntVar()
        self.var_show_triangles.set(1)

        self.var_show_point_indizes = IntVar()

        self.left_panel1 = PanedWindow(self.root)
        self.left_panel1.grid(row=1,column=0)

        self.left_panel2 = PanedWindow(self.root)
        self.left_panel2.grid(row=2, column=0)

        self.left_panel3 = PanedWindow(self.root)
        self.left_panel3.grid(row=3, column=0)

        self.test_button = Button(self.root, text='Data', command=self.openFileWindow)
        self.test_button.grid(row=0, column=0)

        self.erase_all_button = Button(self.root, text='EraseAll', command=self.erase_all)
        self.erase_all_button.grid(row=0, column=1)

        self.point_button = Button(self.root, text='0-Simplex', command=self.use_points)
        self.point_button.grid(row=0, column=2)

        self.line_button = Button(self.root, text='1-Simplex', command=self.use_line)
        self.line_button.grid(row=0, column=3)

        self.triangle_button = Button(self.root, text='2-Simplex', command=self.use_triangle)
        self.triangle_button.grid(row=0, column=4)

        self.eraser_button = Button(self.root, text='eraser', command=self.use_eraser)
        self.eraser_button.grid(row=0, column=5)

        self.slider = Scale(self.root, from_=0, to=90, orient='horizontal', command=self.slider_changed)
        self.slider.grid(row=0, column=6)

        self.show_triangles = Checkbutton(self.root, text='Show Triangles', variable=self.var_show_triangles, onvalue=1,
                                          offvalue=0, command= lambda: self.redraw(False),)
        self.show_triangles.grid(row=0, column=7)

        self.show_point_indizes = Checkbutton(self.root, text='Point Numbers', variable=self.var_show_point_indizes, onvalue=1,
                                          offvalue=0, command= lambda: self.redraw(False))
        self.show_point_indizes.grid(row=0, column=8)

        self.plabel = Label(self.left_panel1, text="Points")
        self.plabel.pack()

        self.scrollbar_points = Scrollbar(self.left_panel1)
        self.scrollbar_points.pack(side=RIGHT,fill=BOTH)

        self.plist = Listbox(self.left_panel1, yscrollcommand=self.scrollbar_points.set)
        self.plist.bind('<<ListboxSelect>>', self.onselectp)
        self.plist.pack()

        self.scrollbar_points.config(command=self.plist.yview)

        self.add_point_button = Button(self.left_panel1, text='AddPoint', command=self.AddPoint_3d)
        self.add_point_button.pack(side=BOTTOM)

        self.llabel = Label(self.left_panel2, text="Lines")
        self.llabel.pack()

        self.scrollbar_lines = Scrollbar(self.left_panel2)
        self.scrollbar_lines.pack(side=RIGHT, fill=BOTH)

        self.llist = Listbox(self.left_panel2, yscrollcommand=self.scrollbar_lines.set)
        self.llist.bind('<<ListboxSelect>>', self.onselectl)
        self.llist.pack()

        self.scrollbar_lines.config(command=self.llist.yview)

        self.tlabel = Label(self.left_panel3, text="Triangles")
        self.tlabel.pack()

        self.scrollbar_triangles = Scrollbar(self.left_panel3)
        self.scrollbar_triangles.pack(side=RIGHT, fill=BOTH)

        self.tlist = Listbox(self.left_panel3, yscrollcommand=self.scrollbar_triangles.set)
        self.tlist.bind('<<ListboxSelect>>', self.onselectt)
        self.tlist.pack()

        self.scrollbar_triangles.config(command=self.tlist.yview)

        self.add_line_button = Button(self.left_panel2, text='AddLine', command=self.AddLine_3d)
        self.add_line_button.pack(side=BOTTOM)

        self.add_triangle_button = Button(self.left_panel3, text='AddTriangle', command=self.AddTriangle_3d)
        self.add_triangle_button.pack(side=BOTTOM)

        self.delete_selection_button = Button(self.root, text='DeleteSelection', command=self.delete_selection)
        self.delete_selection_button.grid(row=4, column=0)

        self.save_button = Button(self.root, text='SaveData', command=self.save_Data)
        self.save_button.grid(row=0,column=9)

        self.c = Canvas(self.root, bg='white', width=700, height=700)
        self.c.grid(row=1, rowspan=7, column=1, columnspan=6)

        self.setup()
        self.root.mainloop()

    # setup method for start
    def setup(self):
        self.update_matrices()
        self.distance = 1000
        self.eraser_on = False
        self.Basepoint = [0, 0, 0]
        self.active_button = self.test_button
        self.c.bind('<Button-1>', self.paint)
        self.update_plain()

    # method to redraw the image. calls 2d redraw or 3d redraw depending on the entries of the first point
    # also gets called sometimes just to redraw and sometimes the homology and the lists need to be updated
    # this is the case if a point/line/triangle is added or deleted.
    def redraw(self, update):
        if len(self.points) != 0:
            if len(self.points[0]) == 3:
                self.redraw3d()
            else:
                self.redraw2d()
        else:
            self.c.delete('all')
        if update:
            self.plist.delete(0, END)
            self.llist.delete(0, END)
            self.tlist.delete(0, END)
            for i in range(len(self.points)):
                self.plist.insert(i, 'P' + str(i) + ': ' + str(self.points[i]))
            for i in range(len(self.lines)):
                self.llist.insert(i, str(self.lines[i]))
            for i in range(len(self.triangles)):
                self.tlist.insert(i, str(self.triangles[i]))
            self.update_matrices()

    # method called when changing the slider to rotate the image
    def slider_changed(self, event):
        self.update_plain()
        self.redraw(False)

    # use point button
    def use_points(self):
        self.activate_button(self.point_button)

    # use line button
    def use_line(self):
        self.activate_button(self.line_button)
        self.demarkpoints()
        self.redraw(False)

    # use triangle button
    def use_triangle(self):
        self.activate_button(self.triangle_button)
        self.demarkpoints()
        self.redraw(False)

    # method to delete all data, demark everything and empty all listboxes
    def erase_all(self):
        self.points = []
        self.lines = []
        self.triangles = []
        self.marked_point3d = None
        self.marked_point = None
        self.marked_triangle = None
        self.marked_line = None
        self.marked_point2 = None
        self.plist.delete(0, END)
        self.llist.delete(0, END)
        self.tlist.delete(0, END)
        self.redraw(True)

    # method to activate the eraser
    def use_eraser(self):
        self.activate_button(self.eraser_button, eraser_mode=True)

    # method to activate some button of point button, line button, triangle button or eraser button
    def activate_button(self, some_button, eraser_mode=False):
        self.active_button.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.active_button = some_button
        self.eraser_on = eraser_mode

    # method to calculate if two lines intersect
    def schnittpunkt(self, line1, line2):
        p1x = self.points[line1[0]][0]  # coordinates of the 4 endpoints of the lines
        p1y = self.points[line1[0]][1]
        q1x = self.points[line1[1]][0]
        q1y = self.points[line1[1]][1]
        p2x = self.points[line2[0]][0]
        p2y = self.points[line2[0]][1]
        q2x = self.points[line2[1]][0]
        q2y = self.points[line2[1]][1]
        if (q2x-p2x) == 0:  # second line is vertical
            v = [q1x - p1x, q1y - p1y]
            tau = (q2x - p1x)/v[0]
            ysp = p1y + v[1] * tau
            if p2y < ysp < q2y or q2y < ysp < p2y:
                return [q2x, round(ysp)]
        elif line1 == line2:
            return None
        elif q1x == p1x:  # first line is vertical
            v = [q2x - p2x, q2y - p2y]
            tau = (q1x - p2x)/v[0]
            ysp = p2y + v[1] * tau
            if p1y < ysp < q1y or q1y < ysp < p1y:
                return [q1x, round(ysp)]
            return None
        else:  # calculate intersection point and return it as integer after rounding
            tau = ((p2y-p1y)-((p2x-p1x)*(q1y-p1y)/(q1x-p1x)))/(((q2x-p2x)*(q1y-p1y)/(q1x-p1x))-(q2y-p2y))
            phi = ((p1y - p2y) - ((p1x - p2x) * (q2y - p2y) / (q2x - p2x))) / (
                        ((q1x - p1x) * (q2y - p2y) / (q2x - p2x)) - (q1y - p1y))
            if 0 < tau < 1 and 0 < phi < 1:
                return [round(p2x+tau*(q2x-p2x)), round(p2y+tau*(q2y-p2y))]
            else:
                return None

    # method called when user clicks anywhere on the canvas
    def paint(self, event):
        clicked_point = [event.x, event.y]
        if self.active_button == self.point_button:  # draw a point or mark existing point
            if self.marked_point:
                self.demarkpoints()
            if self.find_point(clicked_point):
                point1 = self.find_point(clicked_point)
                self.markpoint(point1,0)
            else:
                self.draw_point(clicked_point)
        elif self.active_button == self.line_button:  # draw a line from the marked point to the clicked point or mark the point
            if self.marked_point:
                if self.find_point(clicked_point):
                    p1 = self.marked_point
                    p2 = self.find_point(clicked_point)
                    self.marked_point = None
                    self.draw_line(p1, p2)
            else:
                if self.find_point(clicked_point):
                    point1 = self.find_point(clicked_point)
                    self.markpoint(point1, 0)
        elif self.active_button == self.triangle_button:  # draw a triangle with the two marked points and the clicked point
            if self.marked_point and self.marked_point2:  # or mark the point
                if self.find_point(clicked_point):
                    p1 = self.marked_point
                    p2 = self.marked_point2
                    self.marked_point = None
                    self.marked_point2 = None
                    p3 = self.find_point(clicked_point)
                    self.draw_triangle(p1, p2, p3)
            elif self.marked_point:
                if self.find_point(clicked_point):
                    point1 = self.find_point(clicked_point)
                    self.markpoint(point1, 1)
            else:
                if self.find_point(clicked_point):
                    point1 = self.find_point(clicked_point)
                    self.markpoint(point1, 0)
        elif self.active_button == self.eraser_button:  # erase the clicked point line or triangle
            if self.find_point(clicked_point):
                point1 = self.find_point(clicked_point)
                self.deletepoint(point1, True)
            elif self.find_line(clicked_point):
                line1 = self.find_line(clicked_point)
                self.deleteline(line1, True)
            elif self.find_triangle(clicked_point):
                triangle1 = self.find_triangle(clicked_point)
                self.deletetriangle(triangle1, True)

    # method to draw a point
    def draw_point(self, point):
        if point not in self.points:
            self.points.append(point)
        self.redraw(True)


    # check if position is near a existing point
    def find_point(self, point):
        for i in range(-5, 5):
            for j in range(-5, 5):
                searchobject = [point[0]+i, point[1]+j]
                if searchobject in self.points:
                    return searchobject
        return None

    # set marked points for drawing triangles and lines
    def markpoint(self, point, nr):
        if nr == 0:
            self.marked_point = point
        else:
            self.marked_point2 = point
        self.redraw(False)

    # demark points
    def demarkpoints(self):
        if self.marked_point:
            self.marked_point = None
        if self.marked_point2:
            self.marked_point2 = None

    # method to add line. if line intersects an already existing line, both lines are cut in half and 4 lines are added
    def draw_line(self, point1, point2):
        if point1 == point2:
            return
        schnittlinienliste = []
        schnittpunktliste = []
        dist_list = []
        index1 = self.points.index(point1)
        index2 = self.points.index(point2)
        if [index1, index2] in self.lines or [index2, index1] in self.lines:  # line already existing
            return
        if len(self.lines) == 0:
            self.lines.append([index1, index2])
            self.demarkpoints()
            self.redraw(True)
        else:
            for i in range(len(self.lines)):  # check for intersecting lines and put them in a list
                if self.schnittpunkt(self.lines[i], [index1, index2]):
                    schnittlinienliste.append(self.lines[i])
                    schnittpunktliste.append(self.schnittpunkt(self.lines[i], [index1, index2]))
            if len(schnittpunktliste) == 0:  # no intersection: just add the line
                self.lines.append([index1, index2])
                self.demarkpoints()
                self.redraw(True)
            else:  # sort the intersecting lines for easier processing
                for i in range(len(schnittpunktliste)):
                    dist = ((point1[0] - schnittpunktliste[i][0]) ** 2 + (point1[1] - schnittpunktliste[i][1]) ** 2) ** 0.5
                    dist_list.append([dist, i])
                dist_list.sort()
                for i in range(len(dist_list)):  # add intersection points
                    self.draw_point((schnittpunktliste[dist_list[i][1]]))
                for i in range(len(dist_list)):  # add the new line intersected in parts
                    if i == 0:
                        index3 = self.points.index(schnittpunktliste[dist_list[i][1]])
                        self.lines.append([index1, index3])
                    if i == len(dist_list) - 1:
                        index3 = self.points.index(schnittpunktliste[dist_list[i][1]])
                        index4 = self.points.index(schnittpunktliste[dist_list[i-1][1]])
                        if len(dist_list) > 1:
                            self.lines.append([index4, index3])
                        self.lines.append([index3, index2])
                    elif i != 0:
                        index3 = self.points.index(schnittpunktliste[dist_list[i-1][1]])
                        index4 = self.points.index(schnittpunktliste[dist_list[i][1]])
                        self.lines.append([index3, index4])
                
                for i in range(len(schnittlinienliste)):  # cut the intersected lines in half
                    index5 = schnittlinienliste[i][0]
                    index6 = self.points.index(schnittpunktliste[i])
                    index7 = schnittlinienliste[i][1]
                    for j in self.triangles:  # cut intersected triangles
                        if index5 in j and index7 in j:
                            triangle_temp_1 = [j[0],j[1],j[2]]
                            triangle_temp_1.remove(index5)
                            triangle_temp_1.append(index6)
                            triangle_temp_2 = [j[0],j[1],j[2]]
                            triangle_temp_2.remove(index7)
                            triangle_temp_2.append(index6)
                            self.triangles.append(triangle_temp_1)
                            self.triangles.append(triangle_temp_2)
                            # t1 = [index6 if x == index7 else x for x in j]
                            # t2 = [index6 if x == index5 else x for x in j]
                            self.deletetriangle(j, False)
                            index = len(self.triangles)
                            self.tlist.insert(index, str(triangle_temp_1))
                            self.tlist.insert(index+1, str(triangle_temp_2))
                            for k in range(3):
                                t1_temp=[triangle_temp_1[0],triangle_temp_1[1],triangle_temp_1[2]]
                                t1_temp.pop(k)
                                if (not t1_temp in self.lines) and (not [t1_temp[1],t1_temp[0]] in self.lines):
                                    self.lines.append(t1_temp)
                                    if self.schnittpunkt(t1_temp, [index1, index2]):
                                        schnittlinienliste.append(t1_temp)
                                        schnittpunktliste.append(self.schnittpunkt(t1_temp, [index1, index2]))
                                t2_temp=[triangle_temp_2[0],triangle_temp_2[1],triangle_temp_2[2]]
                                t2_temp.pop(k)
                                if (not t2_temp in self.lines) and (not [t2_temp[1],t2_temp[0]] in self.lines):
                                    self.lines.append(t2_temp)
                                    if self.schnittpunkt(t2_temp, [index1, index2]):
                                        schnittlinienliste.append(t2_temp)
                                        schnittpunktliste.append(self.schnittpunkt(t2_temp, [index1, index2]))
                            # self.triangles.append(t1)
                            # self.triangles.append(t2)

                    self.deleteline(schnittlinienliste[i], False)
                    index = len(self.lines)
                    l1_temp=[index5,index6]
                    l2_temp=[index6,index7]
                    if  (l1_temp  not  in self.lines) and ([l1_temp[1],l1_temp[0]]  not  in self.lines):
                        self.lines.append(l1_temp)
                    if  (l2_temp  not  in self.lines) and ([l2_temp[1],l2_temp[0]]  not  in self.lines):
                        self.lines.append(l2_temp)
                self.redraw(True)
        self.demarkpoints()

    # method to add triangle if it is not already existing and all three lines do exist
    def draw_triangle(self, point1, point2, point3):
        index1 = self.points.index(point1)
        index2 = self.points.index(point2)
        index3 = self.points.index(point3)
        if [index1,index2,index3] in self.triangles or [index1,index3,index2] in self.triangles or [index2,index1,index3] in self.triangles or [index2,index3,index1] in self.triangles or [index3,index1,index2] in self.triangles or [index3,index2,index1] in self.triangles:
            print('dreieick gibt es schon')
            self.demarkpoints()
            return
        if ([index1, index2] in self.lines or [index2, index1] in self.lines) and ([index1, index3] in self.lines or [index3, index1] in self.lines) and ([index2, index3] in self.lines or [index3, index2] in self.lines):
            index = len(self.triangles)
            self.tlist.insert(index, str([index1, index2, index3]))
            self.triangles.append([index1, index2, index3])
            self.redraw(True)
        else:
            print('Kein Dreieick')
        self.demarkpoints()

    # method to redraw everything in 2d draw mode
    def redraw2d(self):
        self.c.delete('all')  # clear canvas
        for i in range(len(self.points)):  # draw all points
            x1, y1 = (self.points[i][0] - 2), (self.points[i][1] - 2)
            x2, y2 = (self.points[i][0] + 2), (self.points[i][1] + 2)
            self.c.create_oval(x1, y1, x2, y2, fill='black')
            if self.var_show_point_indizes.get() == 1:
                self.c.create_text((x1 + 10, y1 + 5), text=str(i))
        for i in range(len(self.lines)):  # draw all lines
            p1 = self.lines[i][0]
            p2 = self.lines[i][1]
            self.c.create_line(self.points[p1][0], self.points[p1][1], self.points[p2][0], self.points[p2][1], fill='black', capstyle=ROUND, smooth=TRUE,splinesteps=36)
        if self.var_show_triangles.get() == 1:  # optional: draw all triangles
            for i in range(len(self.triangles)):
                p1 = self.triangles[i][0]
                p2 = self.triangles[i][1]
                p3 = self.triangles[i][2]
                points = [self.points[p1][0], self.points[p1][1], self.points[p2][0], self.points[p2][1], self.points[p3][0], self.points[p3][1]]
                self.c.create_polygon(points, outline="black", fill="deepskyblue")
        if self.marked_point:  # draw marked points
            x1, y1 = (self.marked_point[0] - 5), (self.marked_point[1] - 5)
            x2, y2 = (self.marked_point[0] + 5), (self.marked_point[1] + 5)
            self.c.create_oval(x1, y1, x2, y2, fill='black')
        if self.marked_point2:
            x1, y1 = (self.marked_point2[0] - 5), (self.marked_point2[1] - 5)
            x2, y2 = (self.marked_point2[0] + 5), (self.marked_point2[1] + 5)
            self.c.create_oval(x1, y1, x2, y2, fill='black')
        if self.marked_line:  # draw marked line in violet and wider
            line = self.marked_line.split(', ')
            line[0] = int(line[0].split('[')[1])
            line[1] = int(line[1].split(']')[0])
            p1 = self.points[line[0]]
            p2 = self.points[line[1]]
            self.c.create_line(p1[0], p1[1], p2[0], p2[1],
                               fill='violet', capstyle=ROUND, smooth=TRUE, splinesteps=36, width=5)
        if self.marked_triangle:  # draw marked triangle in red
            triangle = self.marked_triangle.split(', ')
            triangle[0] = int(triangle[0].split('[')[1])
            triangle[2] = int(triangle[2].split(']')[0])
            p1 = self.points[triangle[0]]
            p2 = self.points[int(triangle[1])]
            p3 = self.points[triangle[2]]
            points = [p1[0], p1[1], p2[0], p2[1],
                      p3[0], p3[1]]
            self.c.create_polygon(points, outline="black", fill="red")

    # method to delete a point. every line and triangle using this point also gets removed
    def deletepoint(self, point1, update):
        index = self.points.index(point1)
        deletelist = []
        for i in range(len(self.triangles)):
            if index in self.triangles[i]:
                deletelist.append(i)
        for i in range(len(deletelist)):
            self.deletetriangle(self.triangles[deletelist[len(deletelist)-i-1]], False)
        deletelist.clear()
        for i in range(len(self.lines)):
            if index in self.lines[i]:
                deletelist.append(i)
        for i in range(len(deletelist)):
            self.deleteline(self.lines[deletelist[len(deletelist) - i - 1]], False)
        # update indices for triangles and lines:
        for i in range(len(self.triangles)):
            for j in range(len(self.triangles[i])):
                if index < self.triangles[i][j]:
                    self.triangles[i][j] = self.triangles[i][j] - 1
        for i in range(len(self.lines)):
            for j in range(len(self.lines[i])):
                if index < self.lines[i][j]:
                    self.lines[i][j] = self.lines[i][j] - 1
        deletelist.clear()
        self.points.remove(point1)
        self.redraw(update)

    # method to check if clicked point is on an existing line. only for 2d draw mode
    def find_line(self, clicked_point):
        for i in range(len(self.lines)):
            # geradengleichung: ax + by + c = 0 mit b = 1
            p1x = self.points[self.lines[i][0]][0]#ax
            p1y = self.points[self.lines[i][0]][1]#ay
            p2x = self.points[self.lines[i][1]][0]
            p2y = self.points[self.lines[i][1]][1]
            bx = p2x - p1x
            by = p2y - p1y
            vector_length = (bx**2 + by**2)**0.5
            dist1 = ((p1x - clicked_point[0]) ** 2 + (p1y - clicked_point[1]) ** 2) ** 0.5
            dist2 = ((p2x - clicked_point[0]) ** 2 + (p2y - clicked_point[1]) ** 2) ** 0.5
            d = abs(((clicked_point[0]-p1x) * by - (clicked_point[1] - p1y) * bx))/(bx**2+by**2)**0.5
            if d < 3:
                if dist1 < vector_length and dist2 < vector_length:
                    return self.lines[i]

    # method to delete line. Every triangle using this line also gets deleted.
    def deleteline(self, line1, update):
        p1 = line1[0]
        p2 = line1[1]
        deletelist = []
        for i in range(len(self.triangles)):
            if p1 in self.triangles[i] and p2 in self.triangles[i]:
                deletelist.append(i)
        for i in range(len(deletelist)):
            self.deletetriangle(self.triangles[deletelist[len(deletelist)-i-1]], False)
        label = str(line1)
        self.lines.remove(line1)
        self.redraw(update)

    # method to calculate if the clicked point is inside an existing triangle. only for 2d drawing mode
    def find_triangle(self, clicked_point):
        for i in range(len(self.triangles)):
            points = [self.points[self.triangles[i][0]], self.points[self.triangles[i][1]], self.points[self.triangles[i][2]]]
            points.sort()
            if points[1][1] < points[2][1]:
                x = points[1]
                points[1] = points[2]
                points[2] = x
            v12 = points[1][0] - points[0][0], points[1][1] - points[0][1]
            v13 = points[2][0] - points[0][0], points[2][1] - points[0][1]
            v1ck = clicked_point[0] - points[0][0], clicked_point[1] - points[0][1]
            A = np.array([[v12[0], v13[0]],
                          [v12[1], v13[1]]])
            B = np.linalg.inv(A)
            lambda1 = B[0][0] * v1ck[0] + B[0][1] * v1ck[1]
            lambda2 = B[1][0] * v1ck[0] + B[1][1] * v1ck[1]
            if (lambda1 + lambda2) < 1 and lambda1 > 0 and lambda2 > 0:
                return self.triangles[i]

    # method to delete a triangle
    def deletetriangle(self, triangle1, update):
        label = str(triangle1)
        idx = self.tlist.get(0, END).index(label)
        self.tlist.delete(idx)
        self.triangles.remove(triangle1)
        self.redraw(update)

    # method to calculate and display the Homology of the drawn data.
    def update_matrices(self):
        self.A12 = []
        self.A01 = []
        # create matrices. A12 has one column for each triangle and one row for each line. Entries are '1' if line is in
        # triangle, '0' otherwise.
        for i in range(len(self.lines)):
            self.A12.append([])
            for j in range(len(self.triangles)):
                self.A12[i].append(0)
        for i in range(len(self.triangles)):
            if [self.triangles[i][0], self.triangles[i][1]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][0], self.triangles[i][1]])
                self.A12[ind1][i] = 1
            elif [self.triangles[i][1], self.triangles[i][0]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][1], self.triangles[i][0]])
                self.A12[ind1][i] = 1
            if [self.triangles[i][0], self.triangles[i][2]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][0], self.triangles[i][2]])
                self.A12[ind1][i] = 1
            elif [self.triangles[i][2], self.triangles[i][0]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][2], self.triangles[i][0]])
                self.A12[ind1][i] = 1
            if [self.triangles[i][1], self.triangles[i][2]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][1], self.triangles[i][2]])
                self.A12[ind1][i] = 1
            elif [self.triangles[i][2], self.triangles[i][1]] in self.lines:
                ind1 = self.lines.index([self.triangles[i][2], self.triangles[i][1]])
                self.A12[ind1][i] = 1
        # A01 has one column for each line and one row for each point. Entries are '1' if point is in
        # line, '0' otherwise.
        for i in range(len(self.points)):
            self.A01.append([])
            for j in range(len(self.lines)):
                self.A01[i].append(0)
        for i in range(len(self.lines)):
            self.A01[self.lines[i][0]][i] = 1
            self.A01[self.lines[i][1]][i] = 1
        # get ranks of matrices
        if self.A01 != []:
            r1 = getrank((self.A01))
        else:
            r1 = 0
        if self.A12 != []:
            r2 = getrank((self.A12))
        else:
            r2 = 0
        # calculate dimensions of homology
        dimH0 = len(self.points) - r1
        dimH1 = (len(self.lines) - r1) - r2
        dimH2 = len(self.triangles) - r2
        # display chain komplex and homology with plt figures
        fig1 = plt.figure(figsize=(1.5, 3), linewidth=1, edgecolor='black')   
        C0 = (r'$(\mathbb{Z}/2)^{%s}$' % (len(self.points)))
        C1 = (r'$(\mathbb{Z}/2)^{%s}$' % (len(self.lines)))
        C2 = (r'$(\mathbb{Z}/2)^{%s}$' % (len(self.triangles)))
        fig1.suptitle("\n Chain complex")
        # fig1.text(0.02, .4, "$0 \longleftarrow C_0 \longleftarrow C_1 \longleftarrow C_2 \longleftarrow 0$",fontsize=9)
        # fig1.text(0.02, .2, "$0 \longleftarrow $" + C0 + "$\longleftarrow$" + C1 + "$\longleftarrow$" + C2 + "$\longleftarrow 0$",fontsize=9)
        
        fig1.text(.058, .76, "$0$") 
        fig1.text(.03, .68  , "$\downarrow$")
        fig1.text(.03, .6, "$C_2\ \cong\ $" + C2)
        fig1.text(.03, .5, r"$\downarrow$")
        fig1.text(.03, .4, "$C_1\ \cong\ $" + C1) 
        fig1.text(.03, .3, "$\downarrow$")
        fig1.text(.03, .2, "$C_0\ \cong\ $" + C0) 
        fig1.text(.03, .12, "$\downarrow$")
        fig1.text(.058, .04, "$0$") 

        self.h1 = FigureCanvasTkAgg(fig1,
                          master=self.root)
        self.h1.draw()
        self.h1.get_tk_widget().grid(row=1, column=7,columnspan=2,rowspan=3)
        # plt.close(fig1)
        H0 = (r'$(\mathbb{Z}/2)^{%s}$' % (dimH0))
        H1 = (r'$(\mathbb{Z}/2)^{%s}$' % (dimH1))
        H2 = (r'$(\mathbb{Z}/2)^{%s}$' % (dimH2))
        fig2 = plt.figure(figsize=(1.1, 3), linewidth=1, edgecolor='black')
        fig2.suptitle("\nHomology")
        # fig2.text(.02, .4, "$0 \longleftarrow H_0 \longleftarrow H_1 \longleftarrow H_2 \longleftarrow 0$",fontsize=9)
        fig2.text(.1, .6, "$H_2\ \cong\ $" + H2) 
        fig2.text(.1, .4, "$H_1\ \cong\ $" + H1) 
        fig2.text(.1, .2, "$H_0\ \cong\ $" + H0) 
        # fig2.text(.02, .2,
        #           "$0 \longleftarrow $" + H0 + "$\longleftarrow$" + H1 + "$\longleftarrow$" + H2 + "$\longleftarrow 0$",fontsize=9)

        self.h2 = FigureCanvasTkAgg(fig2,
                              master=self.root)
        self.h2.draw()
        self.h2.get_tk_widget().grid(row=1  , column=9,columnspan=1,rowspan=3)
        # plt.close(fig2)

    def get_Data(self):
        self.erase_all()
        with open(self.Datafile, 'r') as file:
            data = file.read()
        Data1 = data.split('delta_1')  # split file at delta_1
        Data2 = Data1[1].split('delta_2') # split file at delta_2
        pointsstr = Data1[0]
        points = pointsstr.split('\n')
        linesstr = Data2[0]
        lines = linesstr.split('\n')
        trianglesstr = Data2[1]
        triangles = trianglesstr.split('\n')
        # now there are 3 lists of strings, one for points, one for lines and one for triangles.
        # each list has one entry in the beginning without data and some in the end.
        if points[1].count(',') == 2:  # 2d mode: one ',' between the coordinates and one end of line
            for i in range(len(points)):
                if i == 0:
                    pass  # first line has no point
                elif i >= len(points)-4:
                    pass
                else:
                    point = points[i].split(', ')
                    point = [int(point[0].split('[')[1]), int(point[1].split(']')[0])]
                    if point in self.points:
                        pass
                    else:
                        self.points.append(point)
        elif points[1].count(',') == 3:
            for i in range(len(points)):
                if i == 0:
                    pass
                elif i >= len(points)-4:
                    pass
                else:
                    point = points[i].split(', ')
                    point = [int(point[0].split('[')[1]), int(point[1]), int(point[2].split(']')[0])]
                    if point in self.points:
                        pass
                    else:
                        self.points.append(point)
        for i in range(len(lines)):
            if i == 0:  # first entry is no line
                pass
            elif i >= len(lines)-4:  # some empty lines in the end
                pass
            else:
                line = lines[i].split(', ')
                line = [int(line[0].split('[')[1]), int(line[1].split(']')[0])]
                if line in self.lines or [line[1], line[0]] in self.lines:
                    pass
                elif line[0] < len(self.points) and line[1] < len(self.points):
                    self.lines.append(line)
        for i in range(len(triangles)):
            if i == 0:
                pass
            elif i >= len(triangles) - 2:
                pass
            else:
                triangle = triangles[i].split(', ')
                t = [int(triangle[0].split('[')[1]), int(triangle[1]), int(triangle[2].split(']')[0])]
                if t in self.triangles:
                    pass
                elif ([t[0], t[1]] in self.lines or [t[1], t[0]] in self.lines) and (
                        [t[1], t[2]] in self.lines or [t[2], t[1]] in self.lines) and (
                        [t[0], t[2]] in self.lines or [t[2], t[0]] in self.lines):
                    self.tlist.insert(i, str(t))
                    self.triangles.append(t)
        self.redraw(True)

    # in 2d mode: clicked item in point list is converted from string to a point and assigned to marked point
    # in 3d mode: clicked item is assigned to marked_point3d
    def onselectp(self, evt):
        for i in self.plist.curselection():
            if len(self.points[0]) == 3:
                if self.marked_point3d == self.plist.get(i):
                    self.marked_point3d = None
                else:
                    self.marked_point3d = self.plist.get(i)
            else:
                Punkt = self.plist.get(i).split(', ')
                Punkt[0] = int(Punkt[0].split('[')[1])
                Punkt[1] = int(Punkt[1].split(']')[0])
                if self.marked_point == Punkt:
                    self.marked_point = None
                else:
                    self.marked_point = Punkt
            self.redraw(False)

    # when item in line list is selected the item is set to marked line or, if it already was,
    # marked line is cleared
    def onselectl(self, evt):
        for i in self.llist.curselection():
            if self.marked_line == self.llist.get(i):
                self.marked_line = None
            else:
                self.marked_line = self.llist.get(i)
            self.redraw(False)

    # when item in triangle list is selected the item is set to marked triangle or, if it already was,
    # marked triangle is cleared
    def onselectt(self, evt):
        for i in self.tlist.curselection():
            if self.marked_triangle == self.tlist.get(i):
                self.marked_triangle = None
            else:
                self.marked_triangle = self.tlist.get(i)
            self.redraw(False)

    # method to draw eyerything in 3d mode
    def redraw3d(self):
        self.c.delete('all')  # delete canvas
        twodpoints = []  # list of all 2d koordinates of the 3d points
        sortlist = []  # list to sort triangles
        for i in range(len(self.points)):  # get 2d koordinates of all points
            p = self.get2dKoordinates(self.points[i])
            twodpoints.append(p)
            sortlist.append([p[2], [p], i])
        for i in range(len(self.lines)):  # draw all lines
            p1 = twodpoints[self.lines[i][0]]
            p2 = twodpoints[self.lines[i][1]]
            sortlist.append([(p1[2] + p2[2]) / 2, [p1, p2]])
        for i in range(len(self.triangles)):  # get all triangles in list to be sorted by distance
            p1 = twodpoints[self.triangles[i][0]]
            p2 = twodpoints[self.triangles[i][1]]
            p3 = twodpoints[self.triangles[i][2]]
            color='yellow'
            if "hat.txt" in self.Datafile:
                if (i>40) and (i<230):
                    if i%24 in [22,23,3,4]:
                        color='red'
                if i in [0,1,2,7,8,9,10,14]:
                    color='red'
            else:
                color="deepskyblue"
            sortlist.append([(p1[2] + p2[2] + p3[2]) / 3, [p1, p2, p3],color])
        sortlist.sort(key=takeFirst, reverse=TRUE)


        for i in range(len(sortlist)):
            if len(sortlist[i][1]) == 3:  # if it is a triangle
                if self.var_show_triangles.get() == 1:
                    p1, p2, p3 = sortlist[i][1][0], sortlist[i][1][1], sortlist[i][1][2]
                    points = [p1[0], p1[1], p2[0], p2[1],
                              p3[0], p3[1]]
                    self.c.create_polygon(points, outline="black", fill=sortlist[i][2])
            elif len(sortlist[i][1]) == 1:  # if it is a point
                p = sortlist[i][1][0]
                scale = 2 + int(round(((1300 - p[2])/150)))  #different point size depending on how far away the point is
                x1, y1 = (p[0] - scale), (p[1] - scale)
                x2, y2 = (p[0] + scale), (p[1] + scale)
                self.c.create_oval(x1, y1, x2, y2, fill='black')
                if self.var_show_point_indizes.get() == 1:  # optional point index display, toggled via checkbox
                    self.c.create_text((x1 + 10, y1 + 5), text=str(sortlist[i][2]))
            else:   # if it is a line
                p1, p2 = sortlist[i][1][0], sortlist[i][1][1]
                self.c.create_line(p1[0], p1[1], p2[0], p2[1],
                           fill='black', capstyle=ROUND, smooth=TRUE, splinesteps=36)
        if self.marked_point3d:  # draw the marked point bigger
            Punkt = self.marked_point3d.split(', ')
            Punkt[0] = int(Punkt[0].split('[')[1])
            Punkt[2] = int(Punkt[2].split(']')[0])
            P2d = self.get2dKoordinates([Punkt[0], int(Punkt[1]), Punkt[2]])
            x1, y1 = (P2d[0] - 10), (P2d[1] - 10)
            x2, y2 = (P2d[0] + 10), (P2d[1] + 10)
            self.c.create_oval(x1, y1, x2, y2, fill='black')
        if self.marked_line:  # draw the marked line bigger and violet
            line = self.marked_line.split(', ')
            line[0] = int(line[0].split('[')[1])
            line[1] = int(line[1].split(']')[0])
            p1 = self.get2dKoordinates(self.points[line[0]])
            p2 = self.get2dKoordinates(self.points[line[1]])
            self.c.create_line(p1[0], p1[1], p2[0], p2[1],
                               fill='violet', capstyle=ROUND, smooth=TRUE, splinesteps=36, width=5)
        if self.marked_triangle:  # draw the marked triangle in red
            triangle = self.marked_triangle.split(', ')
            triangle[0] = int(triangle[0].split('[')[1])
            triangle[2] = int(triangle[2].split(']')[0])
            p1 = self.get2dKoordinates(self.points[triangle[0]])
            p2 = self.get2dKoordinates(self.points[int(triangle[1])])
            p3 = self.get2dKoordinates(self.points[triangle[2]])
            points = [p1[0], p1[1], p2[0], p2[1],
                      p3[0], p3[1]]
            self.c.create_polygon(points, outline="black", fill="red")

    # method to rotate plain using the slider. Only thing to do is to multiply the plain vectors and their normal vector
    # with a rotation matrix and update the eye point afterwards
    def update_plain(self):
        d = self.distance  # distance plain to eye point
        H = self.Basepoint  # 'center' point of plain
        if H[0] == 0 and H[1] == 0:
            v = 0
        else:
            v = math.acos((H[2] / (H[0] ** 2 + H[1] ** 2 + H[2] ** 2) ** 0.5)) - math.pi / 4
        u = math.atan2(H[1], H[0]) + math.pi / 2
        n0 = [math.cos(u) * math.cos(v), math.sin(u) * math.cos(v), math.sin(v)]
        e1 = [-math.sin(u), math.cos(u), 0]
        e2 = [-math.cos(u) * math.sin(v), -math.sin(u) * math.sin(v), math.cos(v)]
        e11 = np.array(e1)
        e22 = np.array(e2)
        n00 = np.array(n0)
        alpha = self.slider.get() * math.pi / 180
        drehmatrix = np.array(
            [[1, 0, 0], [0, math.cos(alpha), math.sin(alpha)], [0, -math.sin(alpha), math.cos(alpha)]])
        self.e1new = np.dot(drehmatrix, e11)
        self.e2new = np.dot(drehmatrix, e22)
        self.n0new = np.dot(drehmatrix, n00)
        self.M = [d * self.n0new[0] + H[0], d * self.n0new[1] + H[1], d * self.n0new[2] + H[2]]

    # method to calculate the 2d coordinates of a 3d point via central projection. H is the 'Center' of the projection
    # plain, e1 and e2 the normed projection plain vectors with the current rotation of the image. M is the point of the
    # viewer, also called 'eye point', also with current rotation.
    def get2dKoordinates(self, point):
        M = self.M
        e1new = self.e1new
        e2new = self.e2new
        H = self.Basepoint
        v = [M[0] - point[0], M[1] - point[1], M[2] - point[2]]  # vector from eye point to current point
        k = self.distance  # distance of the eye point to the projection plain
        d = abs(k - (point[0]*self.n0new[0] + point[1]*self.n0new[1] + point[2]*self.n0new[2]))  # distance of point
        # now solve for intersection of v with projection plain. result are the koordinates in (e1, e2) in the plain
        a = np.array([[e1new[0], e2new[0], -v[0]], [e1new[1], e2new[1], -v[1]], [e1new[2], e2new[2], -v[2]]])
        b = np.array([M[0] - H[0], M[1] - H[1], M[2] - H[2]])
        tau = np.linalg.solve(a, b)
        koord = [round(float(tau[0])), round(float(tau[1]))]
        # shift result into positives and return them together with distance
        koordskaliert = [round(abs(koord[0] + 350)), round(abs(koord[1] + 350)), d]
        return koordskaliert

    # function to open window with file list to choose one file to load and open from files in the /Data folder
    def openFileWindow(self):
        # Toplevel object which will
        # be treated as a new window
        self.FileWindow = Toplevel(self.c)
        # sets the title of the
        # Toplevel widget
        self.FileWindow.title("Files")

        # sets the geometry of toplevel
        self.FileWindow.geometry("500x310")

        # A Label widget to show in toplevel
        Label(self.FileWindow,
              text="Choose File").pack()
        scrollbar = Scrollbar(self.FileWindow)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.Lb1 = Listbox(self.FileWindow,width=100, yscrollcommand=scrollbar.set)
        # folder path

        # dir_path = r'Data'

        base_dir = os.path.dirname(__file__)
        dir_path = os.path.join(base_dir, r'./Data/')

        # list to store files
        res = []
        # Iterate directory
        for path in os.listdir(dir_path):
            # check if current path is a file
            if os.path.isfile(os.path.join(dir_path, path)):
                res.append(path)

        res.remove('.DS_Store')
        res.sort()
        names=[]
        for i in  res:
            names.append(i.replace('.txt','').replace('_',' '))

        # print(res)

        for i in range(len(res)):
            self.Lb1.insert(i+1, names[i])
        btn = Button(self.FileWindow, text='Ok', command=self.selected_item)
        # Placing the button and listbox
        btn.pack(side='bottom')
        self.Lb1.pack(side=LEFT, fill=BOTH)
        scrollbar.config(command=self.Lb1.yview)

    # method which is called after user pushes the DeleteSelection Button. The marked point, line and triangle all get
    # deleted if there are any.
    def delete_selection(self):
        self.Datafile=''
        if self.marked_triangle:
            # marked_triangle is a string, so we first have to get the data as a list
            Dreieck = self.marked_triangle.split(', ')
            Dreieck[0] = Dreieck[0].split('[')[1]
            Dreieck[2] = Dreieck[2].split(']')[0]
            self.marked_triangle = None
            self.deletetriangle([int(Dreieck[0]),int(Dreieck[1]),int(Dreieck[2])], True)
        if self.marked_line:
            # marked_line is a string, so we first have to get the data as a list
            Linie = self.marked_line.split(', ')
            Linie[0] = Linie[0].split('[')[1]
            Linie[1] = Linie[1].split(']')[0]
            self.marked_line = None
            self.deleteline([int(Linie[0]),int(Linie[1])], True)
        if self.marked_point3d:
            # marked_point3d is a string, so we first have to get the data as a list
            Punkt = self.marked_point3d.split(', ')
            Punkt[0] = Punkt[0].split('[')[1]
            Punkt[2] = Punkt[2].split(']')[0]
            self.marked_point3d = None
            self.deletepoint([int(Punkt[0]),int(Punkt[1]),int(Punkt[2])], True)
        if self.marked_point:
            # marked_point is not stored as a string, but as a point
            point = self.marked_point
            self.marked_point = None
            self.deletepoint(point, True)


        
    #method to close the Data window and call the data loading method for the selected datafile.
    def selected_item(self): 
        # folder path

        base_dir = os.path.dirname(__file__)
        dir_path = os.path.join(base_dir, r'./Data/')

        for i in self.Lb1.curselection():
            # self.Datafile = dir_path + (self.Lb1.get(i))
            self.Datafile = dir_path + (self.Lb1.get(i).replace(' ','_')+'.txt')
        self.FileWindow.destroy()
        self.get_Data()

    # method which is called after user pushes the 'AddPoint' button. A new window is created with 3 textfields to input
    # the x- y- and z- coordinate of the point. ideal would be values between -300 and 300
    def AddPoint_3d(self):
        self.newPointWindow = Toplevel(self.c)
        self.newPointWindow.title("NewPoint")

        # sets the geometry of toplevel
        self.newPointWindow.geometry("383x100")

        # A Label widget to show in toplevel
        Label(self.newPointWindow,
              text="AddNewPoint").grid(row = 0, column = 1)
        OKButton = Button(self.newPointWindow, text = 'Confirm', command=self.confirmpoint)
        OKButton.grid(row = 3, column = 1)
        Label(self.newPointWindow,
              text="xValue").grid(row=1, column=0)
        Label(self.newPointWindow,
               text="yValue").grid(row=1, column=1)
        Label(self.newPointWindow,
               text="zValue").grid(row=1, column=2)
        self.entryx = Entry(self.newPointWindow, width=15)
        self.entryx.focus_set()
        self.entryx.grid(row=2, column=0)
        self.entryy = Entry(self.newPointWindow, width=15)
        self.entryy.focus_set()
        self.entryy.grid(row=2, column=1)
        self.entryz = Entry(self.newPointWindow, width=15)
        self.entryz.focus_set()
        self.entryz.grid(row=2, column=2)

        self.newPointWindow.mainloop()

    # method which is called after user pushes confirm button in the new point window. First it gets checked if the point
    # exists already, then it gets added to the point list and the listbox displayed on the left.
    def confirmpoint(self):
        x = int(self.entryx.get())
        y = int(self.entryy.get())
        z = int(self.entryz.get())
        point = [x, y, z]
        if point not in self.points:
            index = len(self.points)
            self.points.append(point)
            self.redraw(True)

    # method which is called after user pushes the 'AddLine' button. A new window is created with 2 textfields to input
    # the indices of the end points of the line
    def AddLine_3d(self):
        self.newLineWindow = Toplevel(self.c)
        self.newLineWindow.title("NewLine")

        # sets the geometry of toplevel
        self.newLineWindow.geometry("362x100") #262 fits the width of the entries

        # A Label widget to show in toplevel
        Label(self.newLineWindow,
              text="AddNewLine").grid(row=0, column=1)
        #confirm button
        OKButton = Button(self.newLineWindow, text='Confirm', command=self.confirmline)
        OKButton.grid(row=3, column=1)
        #2Labels and entries for the 2 endpoints of the new line
        Label(self.newLineWindow,
              text="Point1").grid(row=1, column=0)
        Label(self.newLineWindow,
              text="Point2").grid(row=1, column=2)
        self.entryL1 = Entry(self.newLineWindow, width=15)
        self.entryL1.focus_set()
        self.entryL1.grid(row=2, column=0)
        self.entryL2 = Entry(self.newLineWindow, width=15)
        self.entryL2.focus_set()
        self.entryL2.grid(row=2, column=2)

        self.newLineWindow.mainloop()

    # method which is called after user pushes confirm button in the new line window. First it gets checked if the line
    # exists already, then if both points exist and afterwards it gets added to the
    # line list and the listbox displayed on the left.
    def confirmline(self):
        p1 = int(self.entryL1.get())
        p2 = int(self.entryL2.get())
        line = [p1, p2]
        if p1 < len(self.points) and p2 < len(self.points) and line not in self.lines and [p2, p1] not in self.lines:
            self.lines.append(line)
            self.redraw(True)

#method which is called after user pushes the 'AddTriangle' button. A new window is created with 3 textfields to input
#the indices of the verteces of the triangle
    def AddTriangle_3d(self):
        self.newTriangleWindow = Toplevel(self.c)
        self.newTriangleWindow.title("NewTriangle")

        # sets the geometry of toplevel
        self.newTriangleWindow.geometry("362x100") #262 fits with the width of entries

        # A Label widget to show in toplevel
        Label(self.newTriangleWindow,
              text="AddNewTriangle").grid(row=0, column=1)
        #confirm button
        OKButton = Button(self.newTriangleWindow, text='Confirm', command=self.confirmtriangle)
        OKButton.grid(row=3, column=1)
        #3 labels and entries for the 3 vertex points
        Label(self.newTriangleWindow,
              text="Point1").grid(row=1, column=0)
        Label(self.newTriangleWindow,
              text="Point2").grid(row=1, column=1)
        Label(self.newTriangleWindow,
              text="Point3").grid(row=1, column=2)
        self.entryT1 = Entry(self.newTriangleWindow, width=15)
        self.entryT1.focus_set()
        self.entryT1.grid(row=2, column=0)
        self.entryT2 = Entry(self.newTriangleWindow, width=15)
        self.entryT2.focus_set()
        self.entryT2.grid(row=2, column=1)
        self.entryT3 = Entry(self.newTriangleWindow, width=15)
        self.entryT3.focus_set()
        self.entryT3.grid(row=2, column=2)

        self.newTriangleWindow.mainloop()

#method which is called after user pushes confirm button in the new triangle window. First it gets checked if the triangle
#in any permutation exists already, then if all the lines for the triangle exist and afterwards it gets added to the
#triangle list and the listbox displayed on the left. Entries have to be numbers convertable to integers
    def confirmtriangle(self):
        p1 = int(self.entryT1.get())
        p2 = int(self.entryT2.get())
        p3 = int(self.entryT3.get())
        triangle = [p1,p2,p3]
        if [p1, p2, p3] in self.triangles or [p1, p3, p2] in self.triangles or [p2, p1,p3] in self.triangles or [
            p2, p3, p1] in self.triangles or [p3, p1, p2] in self.triangles or [p3, p2,p1] in self.triangles:
            print('dreieick gibt es schon')
            return
        if ([p1, p2] in self.lines or [p2, p1] in self.lines) and (
                [p1, p3] in self.lines or [p3, p1] in self.lines) and (
                [p2, p3] in self.lines or [p3, p2] in self.lines):
            index = len(self.triangles)
            self.tlist.insert(index, str(triangle))
            self.triangles.append(triangle)
            self.redraw(True)
        else:
            print('Kein Dreieick')

#Method to save current points, lines and triangles as a .txt file
    def save_Data(self):
        i=0
        while(1): #check for first not already existing filename
            if os.path.isfile(r'Data/File'+str(i)+'.txt'):
                i += 1
            else:
                with open('Data/File'+str(i)+'.txt', 'w') as f:
                    f.write('delta_0=[\n')
                    for i in range(len(self.points)):
                        f.write(' ' + str(self.points[i]) + ',\n')
                    f.write(' ]\n\n\ndelta_1=[\n')
                    for i in range(len(self.lines)):
                        f.write(' ' + str(self.lines[i]) + ',\n')
                    f.write(' ]\n\n\ndelta_2=[\n')
                    for i in range(len(self.triangles)):
                        f.write(' ' + str(self.triangles[i]) + ',\n')
                    f.write(']\n')
                return

#method to retrun the rank of a matrix. This rank is calculated for a real valued matrix, therefore the matrix  is first
#gaussed over F2.
def getrank(Matrix):
    if len(Matrix) == 0:
        return 0
    else:
        # Zeilen sortieren
        A = np.array(gauss(Matrix))
        if A.any():
            rank = np.linalg.matrix_rank(A)
        else:
            rank = 0
        return rank
#returns the row-echelon form of the matrix over F2 as the field

def gauss(Matrix):
    n = len(Matrix)
    next_Matrix = []
    Matrix.sort(reverse=True)
    if n == 1 or n == 0:
        return Matrix
    else:
        m = len(Matrix[0])
    if m == 1 or m == 0:
        return Matrix
    else:
        if Matrix[0][0] == 0:
            new_Matrix = [[None] * (m - 1) for v in range(n)]
            for i in range(n):
                for j in range(m-1):
                    new_Matrix[i][j] = Matrix[i][j+1]
            next_Matrix = gauss(new_Matrix)
        else:
            new_Matrix = [[None] * (m - 1) for v in range(n-1)]
            for i in range(n-1):
                if Matrix[i+1][0] == 1:
                    Matrix[i+1] = [(x^y) for (x, y) in zip(Matrix[i+1], Matrix[0])]
            for i in range(n - 1):
                for j in range(m - 1):
                    new_Matrix[i][j] = Matrix[i + 1][j + 1]
            next_Matrix = gauss(new_Matrix)
        Matrixreturn = [[None] * (m) for v in range(n)]
        if Matrix[0][0] == 0:
            for i in range(n):
                Matrixreturn[i][0] = 0
                for j in range(m-1):
                    Matrixreturn[i][j+1] = next_Matrix[i][j]
        else:
            for i in range(n):
                for j in range(m):
                    if i == 0 or j == 0:
                        Matrixreturn[i][j] = Matrix[i][j]
                    else:
                        Matrixreturn[i][j] = next_Matrix[i-1][j-1]
        return Matrixreturn


def takeFirst(elem):
    return elem[0]


#main
if __name__ == '__main__':
    Paint()
