def rect_from_center(x_cm,y_cm,w_cm,h_cm,page_h_cm):
    x=x_cm/2.54; y=(page_h_cm-y_cm)/2.54; w=w_cm/2.54; h=h_cm/2.54
    return x-w/2,y-h/2,x+w/2,y+h/2
