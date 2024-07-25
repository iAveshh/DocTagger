import fitz  # PyMuPDF
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox
import json
import spacy
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class PDFDataExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = None
        self.extracted_data = []
        self.nlp = spacy.load("en_core_web_sm")

    def open_pdf(self):
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def extract_data(self):
        if not self.doc:
            messagebox.showerror("Error", "No PDF document opened")
            return

        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            words = page.get_text("words")

            for word in words:
                text = word[4]
                bbox = word[:4]

                doc = self.nlp(text)
                for ent in doc.ents:
                    self.extracted_data.append({
                        "type": ent.label_,
                        "text": ent.text,
                        "bbox": bbox,
                        "page": page_num
                    })

    def highlight_data(self, output_path="highlighted.pdf"):
        if not self.doc:
            messagebox.showerror("Error", "No PDF document opened")
            return

        for data in self.extracted_data:
            page = self.doc.load_page(data['page'])
            bbox = fitz.Rect(data['bbox'])
            if data['type'] in {"ORG", "PERSON", "GPE"}:
                underline_annot = page.add_rect_annot(bbox)
                underline_annot.set_colors(stroke=(1, 0, 0))  # Set color to red for entities considered as keys
                underline_annot.update()
            else:
                annot = page.add_rect_annot(bbox)
                annot.set_colors(stroke=(0, 1, 0))  # Set color to green for other entities
                annot.update()

        try:
            self.doc.save(output_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save highlighted PDF: {e}")

    def save_extracted_data(self, output_path="extracted_data.json"):
        try:
            with open(output_path, "w") as f:
                json.dump(self.extracted_data, f, indent=4)
            messagebox.showinfo("Success", "Extracted data has been saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save extracted data: {e}")

    def close_pdf(self):
        if self.doc:
            self.doc.close()
            self.doc = None

class PDFValidatorApp:
    def __init__(self, root, pdf_path):
        self.root = root
        self.root.title("PDF Data Validator")
        self.current_page = 0
        self.pdf_path = pdf_path
        self.doc = None
        self.start_x = None
        self.start_y = None
        self.extracted_data = []
        self.validated_data = []
        self.photo_images = []
        self.selected_entity = None
        self.history = []

        self.create_widgets()
        self.process_pdf(self.pdf_path)

    def create_widgets(self):
        style = tb.Style()
        style.theme_use("superhero")

        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.upload_button = tb.Button(frame, text="Upload PDF", command=self.upload_pdf, bootstyle="primary-outline")
        self.upload_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_button = tb.Button(frame, text="Save", command=self.save_data, bootstyle="success-outline")
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.undo_button = tb.Button(frame, text="Undo", command=self.undo_last_change, bootstyle="danger-outline")
        self.undo_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = tb.Button(frame, text="Delete", command=self.delete_selected_entity, bootstyle="danger-outline")
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_button = tb.Button(frame, text="Previous Page", command=self.prev_page, bootstyle="secondary-outline")
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.next_button = tb.Button(frame, text="Next Page", command=self.next_page, bootstyle="secondary-outline")
        self.next_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.root.grid_columnconfigure(0, weight=40)
        self.root.grid_columnconfigure(1, weight=5)
        self.root.grid_columnconfigure(2, weight=55)

        # PDF display area (40%)
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.grid(row=1, column=0, sticky="nsew")

        # Set initial width and height to accommodate landscape PDFs
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill="y")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Gap (5%)
        gap_frame = ttk.Frame(self.root, width=100)
        gap_frame.grid(row=1, column=1, sticky="ns")

        # Extracted data panel (55%)
        self.data_panel = ttk.Frame(self.root, padding="10")
        self.data_panel.grid(row=1, column=2, sticky="nsew")

        self.listbox = Listbox(self.data_panel, width=80, height=40, font=("Helvetica", 10), bg="white")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.data_panel, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill="y")

        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.listbox.yview)

        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

    def process_pdf(self, pdf_path):
        self.pdf_path = pdf_path
        self.extracted_data = []
        self.validated_data = []
        self.selected_entity = None
        self.history = []

        extractor = PDFDataExtractor(self.pdf_path)
        extractor.open_pdf()
        extractor.extract_data()
        extractor.highlight_data()
        extractor.save_extracted_data()
        extractor.close_pdf()

        self.load_extracted_data()
        self.open_pdf()
        self.display_pdf(self.current_page)

    def upload_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.pdf_path:
            self.clear_canvas()
            self.process_pdf(self.pdf_path)

    def open_pdf(self):
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def display_pdf(self, page_num):
        if self.doc:
            page = self.doc.load_page(page_num)
            pix = page.get_pixmap()
            img_data = pix.tobytes("ppm")

            photo = tk.PhotoImage(data=img_data)
            self.photo_images.append(photo)

            # Get the PDF page dimensions
            pdf_width, pdf_height = page.rect.width, page.rect.height

            # Update the canvas size to match the PDF dimensions
            self.canvas.config(width=pdf_width, height=pdf_height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

            self.highlight_page_data(page_num)

    def highlight_page_data(self, page_num):
        if self.doc:
            for data in self.extracted_data:
                if data['page'] == page_num:
                    bbox = fitz.Rect(data['bbox'])
                    color = 'red' if data['type'] in {"ORG", "PERSON", "GPE"} else 'green'
                    width = 3 if data == self.selected_entity else 1  # Bold outline for selected entity
                    self.canvas.create_rectangle(bbox.x0, bbox.y0, bbox.x1, bbox.y1, outline=color, width=width)
                    self.canvas.create_text(bbox.x0, bbox.y0 - 10, text=data['type'], fill=color, anchor=tk.SW)

    def highlight_selected_entity(self):
        if self.selected_entity:
            bbox = fitz.Rect(self.selected_entity['bbox'])
            self.canvas.create_rectangle(bbox.x0, bbox.y0, bbox.x1, bbox.y1, outline="blue", width=3)
            self.canvas.create_text(bbox.x0, bbox.y0 - 10, text=self.selected_entity['type'], fill="blue", anchor=tk.SW)

    def load_extracted_data(self):
        try:
            with open("extracted_data.json", "r") as f:
                self.extracted_data = json.load(f)
                self.refresh_extracted_data_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load extracted data: {e}")

    def refresh_extracted_data_list(self):
        self.listbox.delete(0, tk.END)
        for data in self.extracted_data:
            self.listbox.insert(tk.END, f"Page: {data['page']}, Type: {data['type']}, Text: {data['text']}, BBox: {data['bbox']}")

    def on_listbox_select(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            self.selected_entity = self.extracted_data[selected_index[0]]
            self.current_page = self.selected_entity['page']
            self.display_pdf(self.current_page)
            self.highlight_selected_entity()

    def on_canvas_click(self, event):
        self.start_x, self.start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def on_canvas_drag(self, event):
        if self.start_x and self.start_y:
            self.canvas.delete("rect")
            current_x, current_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.create_rectangle(self.start_x, self.start_y, current_x, current_y, outline="blue", tag="rect")

    def on_canvas_release(self, event):
        if self.start_x and self.start_y:
            end_x, end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

            # Ensure the bounding box coordinates are within PDF dimensions
            page = self.doc.load_page(self.current_page)
            pdf_width, pdf_height = page.rect.width, page.rect.height

            end_x = min(max(end_x, 0), pdf_width)
            end_y = min(max(end_y, 0), pdf_height)
            self.start_x = min(max(self.start_x, 0), pdf_width)
            self.start_y = min(max(self.start_y, 0), pdf_height)

            new_bbox = [self.start_x, self.start_y, end_x, end_y]

            self.history.append({
                "index": self.extracted_data.index(self.selected_entity),
                "bbox": self.selected_entity['bbox'].copy(),
                "text": self.selected_entity['text']
            })

            self.selected_entity['bbox'] = new_bbox
            self.update_extracted_data_text()

            self.start_x, self.start_y = None, None
            self.canvas.delete("rect")
            self.display_pdf(self.current_page)
            self.highlight_selected_entity()

    def update_extracted_data_text(self):
        if not self.selected_entity:
            return

        page = self.doc.load_page(self.selected_entity['page'])
        words = page.get_text("words")
        selected_texts = []
        for word in words:
            word_bbox = fitz.Rect(word[:4])
            selection_bbox = fitz.Rect(self.selected_entity['bbox'])
            if selection_bbox.intersects(word_bbox):
                selected_texts.append(word[4])

        self.selected_entity['text'] = ' '.join(selected_texts)
        self.refresh_extracted_data_list()

    def delete_selected_entity(self):
        if self.selected_entity:
            index = self.extracted_data.index(self.selected_entity)
            del self.extracted_data[index]
            self.selected_entity = None
            self.refresh_extracted_data_list()
            self.display_pdf(self.current_page)

    def undo_last_change(self):
        if self.history:
            last_change = self.history.pop()
            index = last_change["index"]
            self.extracted_data[index]['bbox'] = last_change["bbox"]
            self.extracted_data[index]['text'] = last_change["text"]

            self.refresh_extracted_data_list()
            self.display_pdf(self.current_page)
            self.highlight_selected_entity()

    def save_data(self):
        try:
            with open("validated_output.json", "w") as f:
                json.dump(self.extracted_data, f, indent=4)
            messagebox.showinfo("Success", "Validated data has been saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save validated data: {e}")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.display_pdf(self.current_page)

    def next_page(self):
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.display_pdf(self.current_page)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.photo_images.clear()

    def close_pdf(self):
        if self.doc:
            self.doc.close()
            self.doc = None

def main():
    root = tb.Window(themename="superhero")
    root.geometry("1200x800")

    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if not pdf_path:
        root.destroy()
        return

    app = PDFValidatorApp(root, pdf_path)
    root.mainloop()

if __name__ == "__main__":
    main()
