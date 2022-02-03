from cgitb import text
from PySide6.QtCore import Qt
from numpy.random.mtrand import permutation
from lib.QPhotoViewer import QPhotoViewer, VALID_FORMATS
from lib.QRangeWidgeds import QRangeLS
from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QPalette, QPixmap
from PIL import Image, ImageQt
from numpy.core.fromnumeric import shape, size
import numpy, itertools, math, time

DIGITAL_BW_MODE = 0
DIGITAL_COLOR_MODE = 1
VISUAL_BW_MODE = 2

BW = 0
DITHER = 1

OPEN_FILTER =  "*.jpeg *.jpg *.png *.pmb *.pgm *.ppm *.xbm *.xpm *.bmp ;; *.jpeg *.jpg ;; *.png *.pmb *.pgm *.ppm ;; *.xbm *.xpm ;; *.bmp "
SAVE_FILTER = "*.png *.pmb *.pgm *.ppm *.xbm *.xpm *.bmp ;; *.png *.pmb *.pgm *.ppm ;; *.xbm *.xpm ;; *.bmp "


class ModeSelector(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.addItems(['Digital B&W (Logical XOR)', 'Digital Color (Bitwise XOR)', 'Visual B&W (Logical OR)'])
        self.setFixedWidth(165)


class Generator(QMainWindow):    
    def __init__(self) -> None:
        super(Generator, self).__init__()
        self.setWindowTitle("Generator")
        self.image = None
        self.bw = None
        self.shares = []

      # In Side
       # Title
        in_title = QLabel('<h1> Input </h1>')
        in_title.setAlignment(Qt.AlignCenter)
       # Open Image
        self.open_l = QLineEdit()
        self.open_l.setReadOnly(True)
        button = QPushButton("Open Image")
        button.clicked.connect(self.open_file)
        open_layout = QHBoxLayout()
        open_layout.addWidget(self.open_l)
        open_layout.addWidget(button)
       # Drop info, mode
        lavel = QLabel(f'or Drop Image <i> ({" ".join(VALID_FORMATS)[:-1]}) </i>')
        self.mode_selector = ModeSelector()
        self.mode_selector.currentIndexChanged.connect(self.mode_changed)
        a_layout = QHBoxLayout()
        a_layout.addWidget(lavel)
        a_layout.addWidget(self.mode_selector)
       # Threshold, Toggle View, N Shares
        self.threshold = QRangeLS(0, 255, 127)
        self.threshold.newValue.connect(self.new_threshold)
        self.toggle_view = QPushButton("Toggle View")
        self.toggle_view.setCheckable(True)
        self.toggle_view.toggled.connect(self.view_toggle)
        self.toggle_view.setFixedWidth(75)
        self.bw_mode = QComboBox()
        self.bw_mode.addItems(['B&W', 'Dither'])
        self.bw_mode.currentIndexChanged.connect(self.bw_mode_changed)
        label_s = QLabel('Nº Shares:')
        self.n_shares = QRangeLS(2, 10, 2)
        self.n_shares.newValue.connect(self.n_shares_changed)
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.toggle_view)
        options_layout.addWidget(self.bw_mode)
        options_layout.addWidget(self.threshold)
        options_layout.addWidget(label_s)
        options_layout.addWidget(self.n_shares)
       # Photo Viewer
        self.pv_in = QPhotoViewer(self)
        self.pv_in.photoDropped.connect(self.dropped_paths)
       # Layout
        in_container = QWidget()
        in_layout = QVBoxLayout(in_container)
        in_layout.addWidget(in_title)
        in_layout.addLayout(open_layout)
        in_layout.addLayout(a_layout)
        in_layout.addLayout(options_layout)
        in_layout.addWidget(self.pv_in)

      # Out Side
       # Title
        out_title = QLabel('<h1> Outputs </h1>')
        out_title.setAlignment(Qt.AlignCenter)
       # Save
        lavel = QLabel('File Name:')
        save_layout = QHBoxLayout()
        self.save_l = QLineEdit()
        self.save_b = QPushButton("Save")
        self.save_b.setDisabled(True)
        self.save_b.clicked.connect(self.save_files)
        save_layout.addWidget(lavel)
        save_layout.addWidget(self.save_l)
        save_layout.addWidget(self.save_b)
        self.save_b.setDisabled(True)
       # Generate
        self.generate_b = QPushButton("Generate")
        self.generate_b.clicked.connect(self.generate)
        self.generate_b.setEnabled(False)
        self.generate_b.setFixedWidth(140)
        self.generate_inform = QLabel()
        generate_layout = QHBoxLayout()
        generate_layout.addWidget(self.generate_b, alignment=Qt.AlignLeft)
        generate_layout.addWidget(self.generate_inform, alignment=Qt.AlignRight)
       # Shares LS
        self.shares_l = QLabel('Share:')
        self.show_share = QRangeLS(1, 2, 0)
        self.show_share.newValue.connect(self.view_share)
        self.show_share.setDisabled(True)
        view_layout = QHBoxLayout()
        view_layout.addWidget(self.shares_l)
        view_layout.addWidget(self.show_share)
       # Photo Viewer
        self.pv_out = QPhotoViewer(self)
        self.pv_out.setAcceptDrops(False)
       # Layout
        out_container = QWidget()
        out_layout = QVBoxLayout(out_container)
        out_layout.addWidget(out_title)
        out_layout.addLayout(save_layout)
        out_layout.addLayout(generate_layout)
        out_layout.addLayout(view_layout)
        out_layout.addWidget(self.pv_out)

      # Separator
        vline = QFrame()
        vline.setFrameStyle(QFrame.VLine)
        pal = vline.palette()
        pal.setColor(QPalette.WindowText, QColor(122, 122, 122))
        vline.setPalette(pal)
        vline.setLineWidth(0)

      # Layout
        container = QWidget(self)
        main_layout = QHBoxLayout(container)
        main_layout.addWidget(in_container)
        main_layout.addWidget(vline)
        main_layout.addWidget(out_container)

        self.setCentralWidget(container)
        self.setMinimumSize(1080, 720)
        self.showMaximized()
        container.setContentsMargins(20, 5, 20, 20)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        policy.setHorizontalStretch(1)
        in_container.setSizePolicy(policy)
        out_container.setSizePolicy(policy)
        vline.setFixedWidth(40)
        in_title.setContentsMargins(0, 0, 0, 10)
        out_title.setContentsMargins(0, 0, 0, 10)

  # In Functions
   # Load
    def open_file(self):
        path = QFileDialog.getOpenFileName(self, "Select photo to open", filter=OPEN_FILTER)[0]
        if path != '':
            self.dropped_paths([path])

    def dropped_paths(self, paths):
        self.open_l.setText(paths[0])
        self.generate_b.setEnabled(True)
        self.image = Image.open(paths[0])
        if '.png' in paths[0]:
            self.image = self.image.convert('RGBA')
            background = Image.new('RGBA',  self.image.size, (255,255,255))
            self.image = Image.alpha_composite(background,  self.image).convert('RGB')
        self.generate_mode()
        self.update_in_view(True)

   # Pre Proccesing (Mode)
    def generate_mode(self):
        if self.image != None:
            mode = self.mode_selector.currentIndex()
            if mode == DIGITAL_COLOR_MODE:
                self.generate_inform.setText('<i style=" color:#aa0000"> Color Image loaded. Click `Generate` get the new shares </i>')
            else:
                bw_mode = self.bw_mode.currentIndex()
                if bw_mode == BW:
                    self.generate_inform.setText('<i style=" color:#aa0000"> Black & White generated. Click `Generate` get the new shares </i>')
                    fn = lambda x : 1 if x > self.threshold.value else 0
                    img = self.image.convert('L').point(fn, mode='1')
                    self.bw = numpy.array(img)
                else: # DITHER
                    img = self.image.convert('1', dither=True)
                    self.bw = numpy.array(img)
                    self.generate_inform.setText('<i style=" color:#aa0000"> Dither image generated. Click `Generate` get the new shares </i>')

   # View
    def update_in_view(self, fit):
        if self.image != None:
            mode = self.mode_selector.currentIndex()
            if mode == DIGITAL_COLOR_MODE:
                pix = QPixmap.fromImage(ImageQt.ImageQt(self.image))
                self.pv_in.setPhoto(pix, fit)
            else: # DIGITAL_BW_MODE, VISUAL_B&W_MODE
                if self.toggle_view.isChecked():
                    pix = QPixmap.fromImage(ImageQt.ImageQt(self.image))
                    self.pv_in.setPhoto(pix, fit)
                else:
                    img = Image.fromarray(self.bw, 'L')
                    pix = QPixmap.fromImage(ImageQt.ImageQt(img))
                    self.pv_in.setPhoto(pix, fit)
            
    def view_toggle(self, _):
        if self.image != None and self.bw.any():
            self.update_in_view(False)

    def new_threshold(self):
        if self.image != None:
            self.generate_mode()
            self.update_in_view(False)

    def bw_mode_changed(self):
        self.mode_changed(self.mode_selector.currentIndex())

   # N Shares changed
    def n_shares_changed(self):
        if self.image != None:
            self.generate_inform.setText('<i style=" color:#aa0000"> N Shares changed. Click `Generate` get the new shares </i>')

   # Mode
    def mode_changed(self, i):
        if i == DIGITAL_COLOR_MODE:
            self.threshold.setDisabled(True)
            self.toggle_view.setDisabled(True)
            self.bw_mode.setDisabled(True)
            self.n_shares.max = 10
        else: # DIGITAL_BW_MODE & VISUAL_BW_MODE
            bw_mode = self.bw_mode.currentIndex()
            if bw_mode == BW:
                self.threshold.setEnabled(True)
            else: # DITHER
                self.threshold.setDisabled(True)
            self.bw_mode.setEnabled(True)
            self.toggle_view.setEnabled(True)
            self.generate_mode()
            if i == VISUAL_BW_MODE:
                self.n_shares.max = 4
            else:
                self.n_shares.max = 10
        if self.image != None:
            self.generate_inform.setText('<i style=" color:#aa0000"> Generation mode changed. Click `Generate` get the new shares </i>')
            self.update_in_view(True)

  # Out Functions
   # Save and View
    def save_files(self):
        path = QFileDialog.getSaveFileName(self, 'Save shares', 'out/'+self.save_l.text(), filter=SAVE_FILTER)[0]
        if path != '':
            for i in range(self.n_shares.value):
                img = Image.fromarray(self.shares[i])
                tmp_path = path.split('.')
                tmp_path[-2] += f'_{i}'
                img.save('.'.join(tmp_path))
        
            mode = self.mode_selector.currentIndex()
            if mode == DIGITAL_BW_MODE or mode == VISUAL_BW_MODE:
                img = Image.fromarray(self.bw)
            elif mode == DIGITAL_COLOR_MODE:
                img = self.image
            tmp_path = path.split('.')
            tmp_path[-2] += f'_source'
            img.save('.'.join(tmp_path))
             
    def view_share(self):
        i = self.show_share.value - 1
        mode = self.mode_selector.currentIndex()
        if mode == DIGITAL_COLOR_MODE:
            img = Image.fromarray(self.shares[i], 'RGB')
        else: # DIGITAL_BW_MODE & VISUAL_BW_MODE
            img = Image.fromarray(self.shares[i].astype('uint8')*255, 'L')
        pix = QPixmap.fromImage(ImageQt.ImageQt(img))
        self.pv_out.setPhoto(pix)
  
   # Generate
    def generate(self):
        start = time.time()
        self.shares = []

        mode = self.mode_selector.currentIndex()
        if mode == DIGITAL_BW_MODE:
            self.logical_xor()
        elif mode == DIGITAL_COLOR_MODE:
            self.bitwise_xor()
        else:
            self.generate_visual()
        
        self.generate_inform.setText(f'<i style=" color:#00aa00"> Shares generated in {time.time() - start:.3f} s</i>')
        
        # Enable options
        self.show_share.setEnabled(True)
        self.save_b.setEnabled(True)
        self.show_share.max = self.n_shares.value
        self.shares_l.setText(self.mode_selector.currentText()+' Share:')
        self.view_share()

    def logical_xor(self):
        # Generate random S_1, ... S_(i-1)
        shape = self.bw.shape
        for i in range(self.n_shares.value-1):
            self.forceInformUpdate(f'<i style=" color:#aa0000"> Generating shares 1..i-1 (share: {i}) </i>')
            share = numpy.random.choice([False, True], shape)
            self.shares.append(share)

        # S = sum(S_1, ..., S_i) --> S_i = S + sum(s_1, ..., S_(i-1))
        share_n = numpy.copy(self.bw)
        for i in range(self.n_shares.value-1):
            self.forceInformUpdate(f'<i style=" color:#aa0000"> Generating shares i (combining share: {i}) </i>')
            share_n = numpy.logical_xor(share_n, self.shares[i])
        self.shares.append(share_n)

    def bitwise_xor(self):
        source = numpy.array(self.image)
        # Generate random S_1, ... S_(i-1)
        shape = source.shape
        for i in range(self.n_shares.value-1):
            self.forceInformUpdate(f'<i style=" color:#aa0000"> Generating shares 1..i-1 (share: {i}) </i>')
            share = numpy.random.randint(0, 255, shape, dtype=numpy.uint8())
            self.shares.append(share)

        # S = sum(S_1, ..., S_i) --> S_i = S + sum(s_1, ..., S_(i-1))
        share_n = source
        for i in range(self.n_shares.value-1):
            self.forceInformUpdate(f'<i style=" color:#aa0000"> Generating shares i (combining share: {i}) </i>')
            share_n = numpy.bitwise_xor(share_n, self.shares[i])
        self.shares.append(share_n)    

    def generate_visual(self):
      # Source: https://doi.org/10.1007/BFb0053419

      # Parameters
        self.forceInformUpdate('<i style=" color:#aa0000"> Generating Parameters.</i>')
        k = self.n_shares.value
        W = list(range(1, k+1))
        pi = []
        sigma = []
        for i in range(0, len(W)+1):
            # Combinations of size i from W elements
            listing = [list(subset) for subset in itertools.combinations(W, i)]
            if (len(listing[0])%2 == 0):
                pi.extend(listing)
            else:
                sigma.extend(listing)
        pi[0] = [0]
        S0 = make_S(W, pi)
        S1 = make_S(W, sigma)
    
      # Generate empty shares
        self.forceInformUpdate('<i style=" color:#aa0000"> Generating Empty Shares.</i>')
        subpixel_size = math.ceil(math.sqrt(len(S0[0])))
        C_len = pow(subpixel_size, 2)
        h, w = self.bw.shape
        self.shares = []
        for _ in range(self.n_shares.value): # O(k)
            self.shares.append( numpy.zeros((h*subpixel_size, w*subpixel_size), dtype=numpy.bool8()) )

      # Compute
        Scols = S0.shape[1]
        text_timer = time.time()
        self.forceInformUpdate(f'<i style=" color:#aa0000"> Computing Pixel 0,0</i>')
        for i in range(h):
            for j in range(w):
                if time.time()-text_timer > 1:
                    self.forceInformUpdate(f'<i style=" color:#aa0000"> Computing Pixel {i},{j}</i>')
                    text_timer = time.time()
                if self.bw[i][j] == 1: # White
                    C = numpy.take(S0, numpy.random.permutation(Scols), axis=1, out=S0) # Fastest way to permute
                else: # Black
                    C = numpy.take(S1, numpy.random.permutation(Scols), axis=1, out=S1) # Fastest way to permute
                C_ext = C
                while C_ext.shape[1] < C_len: # Extend C so pixel can be divided and still squared
                    C_ext = numpy.append(C_ext, C, 1)
                C_ext = C_ext[:,:C_len] # Get only needed values for squared pixel
                for l in range(k): # Distribute the pixel to each share
                    subpixel = C_ext[l].reshape(-1, subpixel_size)
                    self.shares[l][ i*subpixel_size:(i+1)*subpixel_size, j*subpixel_size:(j+1)*subpixel_size] = subpixel

    def forceInformUpdate(self, str:str):
        self.generate_inform.setText(str)
        app.processEvents()
        
def make_S(W, set): 
    rows = len(W)
    columns = pow(2, rows-1)
    S = numpy.ones((rows, columns), dtype=numpy.bool8())
    for i in range(rows): # O(row*columns)
        for j in range(columns):
            if W[i] in set[j]: # S0[i][j] = 1 iff W[i] in set[j]
                S[i,j] = 0
    return S


class Combiner(QMainWindow):    
    def __init__(self) -> None:
        super(Combiner, self).__init__()
        self.setWindowTitle("Combiner")
        self.shares = []
        self.image = None
        self.size = [0, 0]

      # In Side
       # Title
        in_title = QLabel('<h1> Inputs </h1>')
        in_title.setAlignment(Qt.AlignCenter)
       # Drop info, add shares, clear shares
        lavel = QLabel(f'Drop Shares <i> ({" ".join(VALID_FORMATS)[:-1]}) </i> or')
        add = QPushButton("Add Shares")
        add.clicked.connect(self.add_pressed)
        clear = QPushButton("Clear Shares")
        clear.clicked.connect(self.reset)
        open_layout = QHBoxLayout()
        open_layout.addWidget(lavel)
        open_layout.addWidget(add)
        open_layout.addWidget(clear)
       # Share LS, Size, mode selector
        label_s = QLabel('Share:')
        self.show_share = QRangeLS()
        self.show_share.newValue.connect(self.view_share)
        self.size_l = QLabel()
        self.mode_selector = ModeSelector()
        self.mode_selector.currentIndexChanged.connect(self.mode_changed)
        options_layout = QHBoxLayout()
        options_layout.addWidget(label_s)
        options_layout.addWidget(self.show_share)
        options_layout.addWidget(self.size_l)
        options_layout.addWidget(self.mode_selector)
       # Box selector
        self.list_paths = QComboBox()
        self.list_paths.currentIndexChanged.connect(self.list_index_changed)
        self.remove = QPushButton('-')
        self.remove.clicked.connect(self.remove_share)
        self.remove.setFixedWidth(25)
        list_layout = QHBoxLayout()
        list_layout.addWidget(self.list_paths)
        list_layout.addWidget(self.remove)
       # Photo Viewer
        self.pv_in = QPhotoViewer(self)
        self.pv_in.photoDropped.connect(self.dropped_paths)
       # Layout
        in_container = QWidget()
        in_layout = QVBoxLayout(in_container)
        in_layout.addWidget(in_title)
        in_layout.addLayout(open_layout)
        in_layout.addLayout(options_layout)
        in_layout.addLayout(list_layout)
        in_layout.addWidget(self.pv_in)

      # Out Side
       # Title
        out_title = QLabel('<h1> Output </h1>')
        out_title.setAlignment(Qt.AlignCenter)
       # Save
        lavel = QLabel('File Name:')
        save_layout = QHBoxLayout()
        self.save_l = QLineEdit()
        self.save_b = QPushButton("Save Image")
        self.save_b.clicked.connect(self.save_file)
        save_layout.addWidget(lavel)
        save_layout.addWidget(self.save_l)
        save_layout.addWidget(self.save_b)
       # Combine
        self.combine_b = QPushButton("Combine")
        self.combine_b.clicked.connect(self.combine)
        self.combine_b.setFixedWidth(140)
        self.combine_inform = QLabel()
        generate_layout = QHBoxLayout()
        generate_layout.addWidget(self.combine_b, alignment=Qt.AlignLeft)
        generate_layout.addWidget(self.combine_inform, alignment=Qt.AlignRight)
       # Photo Viewer
        self.pv_out = QPhotoViewer(self)
        self.pv_out.setAcceptDrops(False)
       # Layout
        out_container = QWidget()
        out_layout = QVBoxLayout(out_container)
        out_layout.addWidget(out_title)
        out_layout.addLayout(save_layout)
        out_layout.addLayout(generate_layout)
        out_layout.addWidget(self.pv_out)

      # Separator
        vline = QFrame()
        vline.setFrameStyle(QFrame.VLine)
        pal = vline.palette()
        pal.setColor(QPalette.WindowText, QColor(122, 122, 122))
        vline.setPalette(pal)
        vline.setLineWidth(0)

      # Layout
        self.reset()
        container = QWidget(self)
        main_layout = QHBoxLayout(container)
        main_layout.addWidget(in_container)
        main_layout.addWidget(vline)
        main_layout.addWidget(out_container)

        self.setCentralWidget(container)
        self.setMinimumSize(1080, 720)
        container.setContentsMargins(20, 5, 20, 20)
        container.setContentsMargins(20, 5, 20, 20)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        policy.setHorizontalStretch(1)
        in_container.setSizePolicy(policy)
        out_container.setSizePolicy(policy)
        vline.setFixedWidth(40)
        in_title.setContentsMargins(0, 0, 0, 10)
        out_title.setContentsMargins(0, 0, 0, 10)
        generate_layout.setContentsMargins(0, 0, 0, 27)

  # In functions
   # Load
    def add_pressed(self):
        paths = QFileDialog.getOpenFileNames(self, "Select photo to open", filter=OPEN_FILTER)[0]
        if paths != []:
            self.dropped_paths(paths)

    def dropped_paths(self, paths):
        self.combine_b.setEnabled(True)
        self.show_share.setEnabled(True)
        self.combine_inform.setText('<i style=" color:#aa0000"> New Shares added. Click `Combine` to see the hiden Image </i>')
        self.add_shares(paths)

    def add_shares(self, paths):
        size_invalids = []
        for path in paths:
            img = Image.open(path)
            if self.size == [0, 0]:
                self.update_size(img.size)
            if self.size == img.size:
                self.shares.append(numpy.array(img))
                self.list_paths.addItem(path)
            else:
                size_invalids.append(path)
        if size_invalids != []:
            self.view_share(False)
            msg = f"The following images don't match the Shares sizes ({self.size[0]}w {self.size[0]}h)\n"
            for path in size_invalids:
                msg += f'\n - {path}'
            QMessageBox.warning(self, "Size Images Error", msg, QMessageBox.Ok)
        self.show_share.min = 1
        self.show_share.max = len(self.shares)
   
   # Reset
    def reset(self):
        self.shares = []
        self.update_size([0, 0])
        self.show_share.setDisabled(True)
        self.pv_in.setPhoto(None)
        self.pv_out.setPhoto(None)
        self.combine_inform.setText('')
        self.save_b.setDisabled(True)
        self.combine_b.setEnabled(False)
        self.list_paths.clear()

    def remove_share(self):
        i = self.list_paths.currentIndex()
        del self.shares[i]
        if len(self.shares) == 0:
            self.reset()
        else:
            self.list_paths.removeItem(i)
            self.show_share.max = len(self.shares)
   
   # View
    def view_share(self, update_list_paths=True):
        if self.shares != []:
            i = self.show_share.value - 1
            img = Image.fromarray(self.shares[i])
            pix = QPixmap.fromImage(ImageQt.ImageQt(img))
            self.pv_in.setPhoto(pix)
            if update_list_paths and self.list_paths.currentIndex() != i:
                self.list_paths.setCurrentIndex(i)
        else:
            self.pv_in.setPhoto(None)

    def list_index_changed(self, i):
        self.show_share.value = i+1
        self.view_share(False)

    def update_size(self, size):
        self.size = size
        self.size_l.setText(f'Size: {size[0]}w {size[1]}h')
   
   # Mode
    def mode_changed(self, _):
        if self.shares != []:
            self.combine_inform.setText('<i style=" color:#aa0000"> Combine mode changed. Click `Combine` to see the hiden Image </i>')

  # Out functions
    def save_file(self):
        path = QFileDialog.getSaveFileName(self, 'Save combined image', 'out/'+self.save_l.text(), filter=SAVE_FILTER)[0]
        if path != '':
            img = Image.fromarray(self.image)
            img.save(path)

    def combine(self):
        try:
            mode = self.mode_selector.currentIndex()
            if mode == DIGITAL_BW_MODE:
                self.combine_bw()
            elif mode == DIGITAL_COLOR_MODE:
                self.combine_color()
            else: # VISUAL_BW_MODE
                self.combine_visual()
        except Exception as e:
            print(e)
            self.combine_inform.setText('<i style=" color:#aa0000"> Wrong mode selected to combine the Shares </i>')
        else:
            self.combine_inform.setText('<i style=" color:#00aa00"> Shares combined </i>')
            self.save_b.setEnabled(True) 
    
    def combine_bw(self):
        # S = sum(S_1, ..., S_i)
        self.image = self.shares[-1]
        for i in range(self.show_share.max-1):
            self.image = numpy.logical_xor(self.image, self.shares[i])
        
        img = Image.fromarray(self.image.astype('uint8')*255, 'L')
        pix = QPixmap.fromImage(ImageQt.ImageQt(img))
        self.pv_out.setPhoto(pix)

    def combine_color(self):
        # S = sum(S_1, ..., S_i)
        self.image = self.shares[-1]
        for i in range(self.show_share.max-1):
            self.image = numpy.bitwise_xor(self.image, self.shares[i])
        
        img = Image.fromarray(self.image)
        pix = QPixmap.fromImage(ImageQt.ImageQt(img))
        self.pv_out.setPhoto(pix)

    def combine_visual(self):
        # S = sum(S_1, ..., S_i)
        self.image = self.shares[-1]
        for i in range(self.show_share.max-1):
            self.image = numpy.logical_and(self.image, self.shares[i])
        
        img = Image.fromarray(self.image.astype('uint8')*255, 'L')
        pix = QPixmap.fromImage(ImageQt.ImageQt(img))
        self.pv_out.setPhoto(pix)


class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Image Secret Sharing")

        tabs = QTabWidget()
        tabs.addTab(Generator(), 'Generator')
        tabs.addTab(Combiner(), 'Combiner')
        # self.setStyleSheet('QMainWindow {background: #ffffff}')

        self.setCentralWidget(tabs)
        self.setMinimumSize(1280, 740)

if __name__ == '__main__':
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
