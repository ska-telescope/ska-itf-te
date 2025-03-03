class PlantUMLSequenceDiagram:
    def __init__(self):
        self.diagram_code = ""

    def start_diagram(self, title, actor):
        self.diagram_code = "@startuml SequenceDiagram\n"
        self.diagram_code += 'skinparam ParticipantPadding 10\n'
        self.diagram_code += f"title {title}\n"
        self.diagram_code += f"actor {actor}\n"

    def add_participant(self, participant):
        self.diagram_code += f"participant {self.clean_text(participant)}\n"

    def add_box(self, box_name, colour):
        self.diagram_code += f'box {box_name} #{colour}\n'

    def end_box(self):
        self.diagram_code += 'end box\n'

    def end_diagram(self):
        self.diagram_code += "@enduml"

    def clean_text(self, text):
        return text.replace("-", "_")

    def wrap_text(self, text, max_width=30, max_length=500):
        if max_width <= 0:
            raise ValueError("max_width must be a positive integer.")

        if len(text) > max_length:
            truncated_length = max_length - 3
            text = text[:truncated_length] + "..."

        lines = []
        for i in range(0, len(text), max_width):
            end_index = i + max_width
            segment = text[i:end_index]
            lines.append(segment)

        result = "\n".join(lines).encode("unicode_escape").decode("utf-8")
        return result

    def wrap_text_on_spaces_and_underscores(self, text, max_width=25):
        if max_width <= 0:
            raise ValueError("max_width must be a positive integer.")

        words = text.split(" ")
        line = ""
        lines = []

        for word in words:
            if len(word) > max_width:
                smaller_words = word.split('_')
                for smaller_word in smaller_words:
                    if len(line) + len(smaller_word) < max_width:
                        line += f'_{smaller_word}'
                    else:
                        start_of_split: bool = smaller_word in smaller_words[0] or smaller_words[0] in line
                        lines.append(line if start_of_split else f'_{line}') 
                        line = smaller_word
                
            elif len(line) + len(word) < max_width:
                line += " " + word
            else:
                lines.append(line)
                line = word
        lines.append(line)

        result = "\n".join(lines).encode("unicode_escape").decode("utf-8")
        return result

    def add_note_over(self, device, note, color="lightgreen"):
        device = self.clean_text(device)
        # note = self.wrap_text(note)

        self.diagram_code += f"rnote over {device} #{color}: {note}\n"

    def add_hexagon_note_over(self, device, note, color="lightgrey"):
        device = self.clean_text(device)
        # note = self.wrap_text(note)

        self.diagram_code += f"hnote over {device} #{color}: {note}\n"

    def add_command_call(self, from_device, to_device, note):
        from_device = self.clean_text(from_device)
        to_device = self.clean_text(to_device)
        note = self.wrap_text_on_spaces_and_underscores(note)

        self.diagram_code += f"{from_device} -> {to_device}: {note}\n"

    def add_command_response(self, from_device, to_device, note):
        from_device = self.clean_text(from_device)
        to_device = self.clean_text(to_device)
        note = self.wrap_text_on_spaces_and_underscores(note)

        self.diagram_code += f"{from_device} --> {to_device}: {note}\n"

    def add_divider(self, divider_name: str):
        self.diagram_code += f'== {divider_name} ==\n'

    def add_new_page(self, page_title: str):
        self.diagram_code += f'newpage {page_title}\n'