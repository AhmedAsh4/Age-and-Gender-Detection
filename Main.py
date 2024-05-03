import tkinter as tk
from tkcalendar import DateEntry
from tkinter import messagebox, filedialog
from Database import generate_report
import cv2
from PIL import Image, ImageTk
from prediction import predict_image,predict_camera
from datetime import datetime,timedelta

global window 
window = tk.Tk()

def loadImages(window):
    global inner_frame
    global canvas
    global scrollbar
    global framemini
    try:
        removeImages()
    except:
        pass
    try:
        closeCameraPreview()
    except:
        pass
    imageFiles = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    if imageFiles:
        framemini = tk.Frame(window)
        framemini.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(framemini)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,padx=220)

        scrollbar = tk.Scrollbar(framemini, orient=tk.VERTICAL, command=canvas.yview,width=20,bg='grey')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)

        for file in imageFiles:
            img = predict_image(file)

            imgtk = ImageTk.PhotoImage(image=img)
            imageLabel = tk.Label(inner_frame, image=imgtk)
            imageLabel.image = imgtk
            imageLabel.pack(padx=10, pady=10, side=tk.TOP)

        inner_frame.update_idletasks()
        canvas.configure(scrollregion = canvas.bbox("all"))
    else:
        messagebox.showinfo("No Image", "No image files found in the selected directory.")

def removeImages():
    global inner_frame
    global canvas
    global scrollbar
    global framemini
    if inner_frame:
        inner_frame.destroy()
        inner_frame = None
    if canvas:
        canvas.destroy()
        canvas = None
    if scrollbar:
        scrollbar.destroy()
        scrollbar = None
    if framemini:
        framemini.destroy()
        framemini = None

def openCameraPreview():
    global cap
    try:
        removeImages()
    except:
        pass
    try:
        closeCameraPreview()
    except:
        pass
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showinfo("Error Detected", "Camera Not Available")
    
    def update():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = predict_camera(frame_rgb)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            camera_label.imgtk = imgtk
            camera_label.config(image=imgtk)
            
        camera_label.after(10, update)
    
    camera_label.pack()
    update()


def closeCameraPreview():
    global cap
    if cap:
        cap.release()
        camera_label.pack_forget()
        cap = None 

def createWindow(title, width, height):
    window.title(title)
    window.geometry(f"{width}x{height}")
    return window

def createMainMenuButtons(frame):
    openPredictButton = tk.Button(frame, text="Predict New Data", font=("Helvetica", 22, "bold"), width=40, height=5,borderwidth=10)
    openGenerateButton = tk.Button(frame, text="Generate Report", font=("Helvetica", 22, "bold"), width=40, height=5,borderwidth=10)
    return openPredictButton, openGenerateButton

def createPredictButtons(frame):
    openCameraButton = tk.Button(frame, text="Open Camera", font=("Helvetica", 18, "bold"), width=20, height=2,command=openCameraPreview,borderwidth=10)
    #closeCameraButton = tk.Button(frame, text="Close Camera", font=("Helvetica", 16, "bold"), width=20, height=2,command=closeCameraPreview)
    LoadImageButton = tk.Button(frame, text="Load Images", font=("Helvetica", 18, "bold"), width=20, height=2,command=lambda: loadImages(window),borderwidth=10)
    #closeImageButton = tk.Button(frame, text="Remove Images", font=("Helvetica", 16, "bold"), width=20, height=2, command=removeImages)
    predictToMenuButton = tk.Button(frame, text="Return to Main Menu", font=("Helvetica", 18, "bold"), width=20, height=2,borderwidth=10)
    #return openCameraButton, closeCameraButton, LoadImageButton, closeImageButton, predictToMenuButton
    return openCameraButton, LoadImageButton, predictToMenuButton

def createGenerateReportButtons(frame, mainMenuFrame):
    generateReportButton = tk.Button(frame, text="Generate Report", font=("Helvetica", 16, "bold"), width=20, height=2,borderwidth=10)
    GenerateToMenuButton = tk.Button(frame, text="Return to Main Menu", font=("Helvetica", 16, "bold"), width=20, height=2,borderwidth=10)
    GenerateToMenuButton.config(command=lambda: switchToMainMenu(mainMenuFrame, frame))
    return generateReportButton, GenerateToMenuButton

def createInputTextboxes(frame):
    FileNameLabel = tk.Label(frame, text="File Name:", font=("Helvetica", 16, "bold"))
    FileNameBox = tk.Entry(frame, font=("Helvetica", 16), width=20)

    GendConfLabel = tk.Label(frame, text="Gender Confidence:", font=("Helvetica", 16, "bold"))
    GenderConfBox = tk.Entry(frame, font=("Helvetica", 16), width=20)

    AgeConfLabel = tk.Label(frame, text="Age Confidence:", font=("Helvetica", 16, "bold"))
    AgeConfBox = tk.Entry(frame, font=("Helvetica", 16), width=20)

    return FileNameLabel, FileNameBox, GendConfLabel, GenderConfBox, AgeConfLabel, AgeConfBox

def createDateRangeWidget(frame):
    DateRangeLabel = tk.Label(frame, text="Date Range:", font=("Helvetica", 16, "bold"))
    DateRangeLabel.pack(pady=20)

    DataEntryFrame = tk.Frame(frame)
    DataEntryFrame.pack()

    StartDateBox = DateEntry(DataEntryFrame, font=("Helvetica", 16), width=10,
                             background='darkblue', foreground='white', borderwidth=2,
                             date_pattern='yyyy-mm-dd')
    StartDateBox.delete(0, "end")
    StartDateBox.pack(side=tk.LEFT)

    tk.Label(DataEntryFrame, text="to", font=("Helvetica", 16)).pack(side=tk.LEFT, padx=5)

    EndDateBox = DateEntry(DataEntryFrame, font=("Helvetica", 16), width=10,
                           background='darkblue', foreground='white', borderwidth=2,
                           date_pattern='yyyy-mm-dd')
    EndDateBox.delete(0, "end")
    EndDateBox.pack(side=tk.LEFT)

    return DateRangeLabel, StartDateBox, EndDateBox

def cleanBoxes(FileNameBox,GenderConfBox,AgeConfBox,StartDateBox,EndDateBox):
    FileNameBox.delete(0, tk.END)
    GenderConfBox.delete(0, tk.END)
    AgeConfBox.delete(0, tk.END)
    StartDateBox.delete(0, tk.END)
    EndDateBox.delete(0, tk.END)

def switchToPredictWindow(mainMenuFrame, predictFrame):
    try:
        removeImages()
    except:
        pass
    try:
        closeCameraPreview()
    except:
        pass
    mainMenuFrame.pack_forget()
    predictFrame.pack()

def switchToMainMenu(mainMenuFrame, frame):
    try:
        removeImages()
    except:
        pass
    try:
        closeCameraPreview()
    except:
        pass
    frame.pack_forget()
    mainMenuFrame.pack(expand=True)

def switchToGenerateReportWindow(mainMenuFrame, generateFrame):
    mainMenuFrame.pack_forget()
    generateFrame.pack()

def generateReport(FileNameBox, GenderConfBox, AgeConfBox, StartDateBox, EndDateBox):
    filename = FileNameBox.get()
    genderConfidence = GenderConfBox.get()
    ageConfidence = AgeConfBox.get()
    startDate = StartDateBox.get()
    endDate = EndDateBox.get()

    filename = filename if filename != '' else None
    genderConfidence = float(genderConfidence)/100 if genderConfidence != '' else None
    
    if genderConfidence is not None:
        if genderConfidence > 1.0:
            messagebox.showinfo("Error Detected", "Invalid Gender Confidence (Between 0 and 100)")
            return
    
    ageConfidence = float(ageConfidence)/100 if ageConfidence != '' else None
    
    if ageConfidence is not None:
        if ageConfidence > 1.0:
            messagebox.showinfo("Error Detected", "Invalid Age Confidence (Between 0 and 100)")
            return

    if endDate == '':
        endDate = None
    else:
        endDate = datetime.strptime(endDate, '%Y-%m-%d')
        endDate = endDate + timedelta(days=1)
        endDate = endDate.strftime('%Y-%m-%d')

    generate_report(gendconf=genderConfidence, ageConf=ageConfidence,
                    filename=filename,startdate=startDate,enddate=endDate)


def setupUi(window):
    mainMenuFrame = tk.Frame(window)
    mainMenuFrame.pack(expand=True)

    openPredictButton, openGenerateButton = createMainMenuButtons(mainMenuFrame)
    openPredictButton.pack(pady=20)
    openGenerateButton.pack(pady=20)

    predictFrame = tk.Frame(window)

    #openCameraButton, closeCameraButton, LoadImageButton, closeImageButton, predictToMenuButton = createPredictButtons(predictFrame)
    openCameraButton, LoadImageButton, predictToMenuButton = createPredictButtons(predictFrame)
    openCameraButton.pack(side=tk.LEFT, padx=8,pady=20)
    #closeCameraButton.pack(side=tk.LEFT, padx=8,pady=20)
    LoadImageButton.pack(side=tk.LEFT, padx=8,pady=20)
    #closeImageButton.pack(side=tk.LEFT, padx=8,pady=20)
    predictToMenuButton.pack(side=tk.LEFT, padx=8,pady=20)
        
    openPredictButton.config(command=lambda: switchToPredictWindow(mainMenuFrame, predictFrame))
    predictToMenuButton.config(command=lambda: switchToMainMenu(mainMenuFrame, predictFrame))

    global camera_label
    camera_label = tk.Label(window)
    camera_label.pack(pady=20)
    camera_label.pack_forget()

    generateFrame = tk.Frame(window)

    generateReportButton, GenerateToMenuButton = createGenerateReportButtons(generateFrame, mainMenuFrame)
    GenerateToMenuButton.pack(side=tk.TOP, padx=8,pady=(40,20))
    generateReportButton.pack(side=tk.TOP, padx=8,pady=20)

    #FileNameLabel, FileNameBox, GendConfLabel, GenderConfBox, AgeConfLabel, AgeConfBox = createInputTextboxes(generateFrame)
    FileNameLabel, FileNameBox, _, _, _, _ = createInputTextboxes(generateFrame)
    FileNameLabel.pack(pady=20)
    FileNameBox.pack()
    _, StartDateBox, EndDateBox = createDateRangeWidget(generateFrame)

    _, _, GendConfLabel, GenderConfBox, AgeConfLabel, AgeConfBox = createInputTextboxes(generateFrame)
    GendConfLabel.pack(pady=20)
    GenderConfBox.pack()
    AgeConfLabel.pack(pady=20)
    AgeConfBox.pack()

    def generateReportWrapper():
        generateReport(FileNameBox, GenderConfBox, AgeConfBox, StartDateBox, EndDateBox)
        messagebox.showinfo("Report Generated", "Report generation is complete!")
        cleanBoxes(FileNameBox,GenderConfBox,AgeConfBox,StartDateBox,EndDateBox)

    generateReportButton.config(command=generateReportWrapper)

    openGenerateButton.config(command=lambda: switchToGenerateReportWindow(mainMenuFrame, generateFrame))

def main():
    window = createWindow("Age and Gender Detection", 1080, 720)
    setupUi(window)
    window.mainloop()

if __name__ == "__main__":
    main()
