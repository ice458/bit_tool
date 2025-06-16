# Import necessary libraries
import tkinter as tk
from tkinter import ttk
import sys
import json
import os

# Define the configuration file name
CONFIG_FILE = "./files/bit_tool_config.json"


class BitCalc(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bit Tool")

        # Configure window resizing and layout
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Initialize internal state variables
        self._current_value = 0
        self._is_updating = False  # Flag to prevent recursive updates

        # Initialize Tkinter variables for UI elements
        self.num_bytes_var = tk.IntVar()
        self.hex_var = tk.StringVar()
        self.dec_var = tk.StringVar()
        self.oct_var = tk.StringVar()
        self.bin_var = tk.StringVar()
        self.bit_vars = [tk.IntVar(value=0) for _ in range(64)]  # For bit checkboxes
        self.checkbox_widgets = [None] * 64  # To store checkbox widgets
        self.signed_mode_var = tk.BooleanVar(value=False)  # For signed decimal mode
        self.shift_amount_var = tk.IntVar(value=1)  # For shift/rotate operations

        # Create the main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        main_frame.columnconfigure(0, weight=1)

        # Create UI sections
        self._create_bit_display(main_frame)
        self._create_input_fields(main_frame)
        self._create_controls(main_frame)

        # Create the status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            self, textvariable=self.status_var, anchor=tk.W, padding=(5, 2)
        )
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Set window icon (platform-dependent)
        try:
            if sys.platform == "win32":
                self.iconbitmap("./files/icon.ico")
            else:
                img = tk.PhotoImage(file="./files/icon.png")
                self.tk.call("wm", "iconphoto", self._w, img)
        except tk.TclError:
            self._set_status_message(
                "Note: Icon file not found or invalid. Using default icon."
            )

        # Add trace callbacks for variable changes
        self.num_bytes_var.trace_add("write", self._on_num_bytes_change)
        self.hex_var.trace_add("write", lambda *_: self._update_from_entry("hex"))
        self.dec_var.trace_add("write", lambda *_: self._update_from_entry("dec"))
        self.oct_var.trace_add("write", lambda *_: self._update_from_entry("oct"))
        self.bin_var.trace_add("write", lambda *_: self._update_from_entry("bin"))
        self.signed_mode_var.trace_add("write", lambda *_: self._update_display())

        # Load settings and update the display
        self._load_settings()
        self._update_display()

        # Set action on window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_settings(self):
        # Load settings from the configuration file
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    settings = json.load(f)
                    self.num_bytes_var.set(settings.get("num_bytes", 4))
                    self.signed_mode_var.set(settings.get("signed_mode", False))
                    self.shift_amount_var.set(settings.get("shift_amount", 1))
                self._set_status_message("Settings loaded successfully.")
            except (IOError, json.JSONDecodeError) as e:
                # Handle errors during loading and set default values
                self.num_bytes_var.set(4)
                self.signed_mode_var.set(False)
                self.shift_amount_var.set(1)
                self._set_status_message(
                    f"Error loading settings: {e}. Using defaults."
                )
        else:
            # Set default values if config file doesn't exist
            self.num_bytes_var.set(4)
            self.signed_mode_var.set(False)
            self.shift_amount_var.set(1)
            self._set_status_message("No config file found. Using default settings.")

    def _save_settings(self):
        # Save current settings to the configuration file
        settings = {
            "num_bytes": self.num_bytes_var.get(),
            "signed_mode": self.signed_mode_var.get(),
            "shift_amount": self.shift_amount_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(settings, f)
            self._set_status_message("Settings saved successfully.")
        except IOError as e:
            self._set_status_message(f"Error: Could not save settings: {e}")

    def _on_closing(self):
        # Save settings and close the application
        self._save_settings()
        self.destroy()

    def _validate_input(self, P, base):
        # Generic validation function for numeric input fields
        if P == "":
            return True
        try:
            int(P, base)
            return True
        except ValueError:
            return False

    # Specific validation functions for different bases
    def _validate_hex(self, P):
        return self._validate_input(P, 16)

    def _validate_dec(self, P):
        # Validate decimal input, allowing for negative sign in signed mode
        if self.signed_mode_var.get():
            if P == "-":
                return True
            if P.startswith("-"):
                try:
                    int(P)
                    return True
                except ValueError:
                    return False
            return self._validate_input(P, 10)
        else:
            if P.startswith("-"):  # Disallow negative sign in unsigned mode
                return False
            return self._validate_input(P, 10)

    def _validate_oct(self, P):
        return self._validate_input(P, 8)

    def _validate_bin(self, P):
        return self._validate_input(P, 2)

    def _validate_shift_amount(self, P):
        # Validates that the shift amount is a non-negative integer
        if P == "":
            return True
        try:
            val = int(P)
            return val >= 0
        except ValueError:
            return False

    def _create_bit_display(self, parent):
        # Creates the 8x8 grid of bit checkboxes and labels
        bit_frame = ttk.LabelFrame(parent, text="Bit Display", padding="5")
        bit_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Create 64 checkboxes and their corresponding bit number labels
        for i in range(64):
            byte_num = 7 - (i // 8)  # Calculate byte number (7 down to 0)
            # Determine row and column for layout, grouping by 4 bytes
            checkbox_frame_base_row = 1 - (byte_num // 4)
            actual_checkbox_row = checkbox_frame_base_row * 2 + 1
            byte_group_col_idx = 3 - (byte_num % 4)
            byte_group_col_offset = byte_group_col_idx * 9
            actual_checkbox_col = (i % 8) + byte_group_col_offset

            bit_index = 63 - i  # Bit index (MSB is 63, LSB is 0)

            f = ttk.Frame(bit_frame)  # Frame for each checkbox and label
            f.grid(row=actual_checkbox_row, column=actual_checkbox_col, padx=1)

            cb = ttk.Checkbutton(
                f,
                variable=self.bit_vars[bit_index],
                command=self._update_from_bits,  # Callback when checkbox state changes
            )
            cb.pack()
            self.checkbox_widgets[bit_index] = cb  # Store checkbox widget

            lbl = ttk.Label(f, text=str(bit_index), anchor=tk.CENTER)
            lbl.pack()

        # Add vertical separators between byte groups
        for row_idx in range(2):  # Two rows of byte groups
            separator_row = row_idx * 2 + 1
            for i in range(3):  # Three separators per row
                sep_col = i * 9 + 8
                sep = ttk.Separator(bit_frame, orient="vertical")
                sep.grid(
                    row=separator_row, column=sep_col, sticky="ns", rowspan=2, padx=2
                )

        # Add byte labels (e.g., "8byte", "7byte")
        for i in range(8):
            byte_label_text = f"{8-i}byte"
            actual_label_col = (i % 4) * 9
            actual_label_row = (i // 4) * 2
            lbl = ttk.Label(bit_frame, text=byte_label_text)
            lbl.grid(
                row=actual_label_row, column=actual_label_col, columnspan=8, pady=(5, 0)
            )

    def _create_input_fields(self, parent):
        # Creates the HEX, DEC, OCT, BIN input fields and copy buttons
        input_frame = ttk.LabelFrame(parent, text="Conversions", padding="5")
        input_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        input_frame.columnconfigure(0, weight=0)  # Label column
        input_frame.columnconfigure(1, weight=1)  # Entry column (expandable)
        input_frame.columnconfigure(2, weight=0)  # Copy button column
        input_frame.columnconfigure(3, weight=0)  # Signed checkbox column

        labels = ["HEX", "DEC", "OCT", "BIN"]
        variables = [self.hex_var, self.dec_var, self.oct_var, self.bin_var]
        validation_callbacks = [
            self._validate_hex,
            self._validate_dec,
            self._validate_oct,
            self._validate_bin,
        ]

        for i, (label_text, var, val_cb) in enumerate(
            zip(labels, variables, validation_callbacks)
        ):
            # Create label for the input field
            ttk.Label(input_frame, text=label_text, width=4).grid(
                row=i, column=0, sticky="w", padx=5, pady=2
            )

            # Create entry field with validation
            vcmd = (self.register(val_cb), "%P")  # Validation command
            entry = ttk.Entry(
                input_frame,
                textvariable=var,
                font=("Courier", 10),  # Monospaced font for numbers
                justify="right",  # Right-align text
                validate="key",  # Validate on key press
                validatecommand=vcmd,
            )
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)

            # Create "Copy" button
            copy_button = ttk.Button(
                input_frame,
                text="Copy",
                width=5,
                command=lambda v=var: self._copy_to_clipboard(v.get()),
            )
            copy_button.grid(row=i, column=2, sticky="e", padx=(0, 5), pady=2)

            # Add "Signed" checkbox for the DEC field
            if label_text == "DEC":
                signed_cb = ttk.Checkbutton(
                    input_frame, text="Signed", variable=self.signed_mode_var
                )
                signed_cb.grid(row=i, column=3, sticky="e", padx=(0, 5))

    def _create_controls(self, parent):
        # Creates byte selection radio buttons, bit operation buttons, and action buttons
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        # Configure columns to distribute space
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        # --- Byte Selection Frame ---
        byte_select_frame = ttk.LabelFrame(controls_frame, text="Select Bytes")
        byte_select_frame.grid(row=0, column=0, padx=2, pady=2, sticky="ewns")
        # Create radio buttons for selecting number of bytes (1 to 8)
        for i in range(1, 9):
            row = (i - 1) // 4
            col = (i - 1) % 4
            rb = ttk.Radiobutton(
                byte_select_frame, text=str(i), value=i, variable=self.num_bytes_var
            )
            rb.grid(row=row, column=col, padx=1, pady=1, sticky="w")
        for i in range(4):  # Ensure columns don't expand unnecessarily
            byte_select_frame.columnconfigure(i, weight=0)

        # --- Bit Operations Frame ---
        ops_frame = ttk.LabelFrame(controls_frame, text="Bit Operations")
        ops_frame.grid(row=0, column=1, padx=2, pady=2, sticky="ewns")
        ops_frame.columnconfigure(0, weight=1)
        ops_frame.columnconfigure(1, weight=1)
        ops_frame.columnconfigure(2, weight=1)

        # Shift amount input field
        ttk.Label(ops_frame, text="Amount:").grid(
            row=0, column=0, padx=2, pady=2, sticky="e"
        )
        vcmd_shift = (self.register(self._validate_shift_amount), "%P")
        shift_amount_entry = ttk.Entry(
            ops_frame,
            textvariable=self.shift_amount_var,
            width=5,
            validate="key",
            validatecommand=vcmd_shift,
        )
        shift_amount_entry.grid(
            row=0, column=1, columnspan=2, padx=2, pady=2, sticky="w"
        )

        # Shift and Rotate buttons
        btn_shl = ttk.Button(ops_frame, text="SHL", command=self._shift_left)
        btn_shl.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        btn_lsr = ttk.Button(ops_frame, text="LSR", command=self._shift_right_logical)
        btn_lsr.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        btn_asr = ttk.Button(
            ops_frame, text="ASR", command=self._shift_right_arithmetic
        )
        btn_asr.grid(row=1, column=2, sticky="ew", padx=2, pady=2)

        btn_rol = ttk.Button(ops_frame, text="ROL", command=self._rotate_left)
        btn_rol.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        btn_ror = ttk.Button(ops_frame, text="ROR", command=self._rotate_right)
        btn_ror.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

        # --- Action Buttons Frame ---
        action_button_frame = ttk.LabelFrame(controls_frame, text="Actions")
        action_button_frame.grid(row=0, column=2, padx=2, pady=2, sticky="ewns")

        # Invert, Reverse, Clear buttons
        btn_invert = ttk.Button(
            action_button_frame, text="Invert", command=self._invert_bits
        )
        btn_invert.pack(fill="x", pady=2, padx=2)

        btn_reverse = ttk.Button(
            action_button_frame, text="Reverse", command=self._reverse_bits
        )
        btn_reverse.pack(fill="x", pady=2, padx=2)

        btn_clear = ttk.Button(
            action_button_frame, text="Clear", command=self._clear_bits
        )
        btn_clear.pack(fill="x", pady=2, padx=2)

    def _get_mask(self):
        # Returns a bitmask for the current number of selected bytes
        num_bits = self.num_bytes_var.get() * 8
        return (1 << num_bits) - 1

    def _update_from_entry(self, source):
        # Callback when a value in an entry box (HEX, DEC, OCT, BIN) is changed
        if self._is_updating:  # Prevent recursion
            return

        base_map = {"hex": 16, "dec": 10, "oct": 8, "bin": 2}
        var_map = {
            "hex": self.hex_var,
            "dec": self.dec_var,
            "oct": self.oct_var,
            "bin": self.bin_var,
        }

        value_str = var_map[source].get().strip()
        if not value_str:  # If entry is empty, set value to 0
            self._current_value = 0
        else:
            try:
                # Handle signed decimal input separately
                if source == "dec" and self.signed_mode_var.get():
                    num_val = int(value_str, 10)
                    num_bits = self.num_bytes_var.get() * 8
                    if num_val < 0:  # Negative number
                        # Check if within representable range for two's complement
                        if num_val >= -(1 << (num_bits - 1)):
                            self._current_value = (
                                1 << num_bits
                            ) + num_val  # Convert to two's complement
                        else:
                            # If out of range, truncate (behavior might need review for strictness)
                            self._current_value = num_val & self._get_mask()
                    else:  # Positive number
                        # Check if within representable range for signed
                        if num_val < (1 << (num_bits - 1)):
                            self._current_value = num_val
                        else:
                            # If out of range, truncate
                            self._current_value = num_val & self._get_mask()
                else:  # For HEX, OCT, BIN, or unsigned DEC
                    self._current_value = int(value_str, base_map[source])
            except ValueError:
                # If conversion fails (e.g., invalid characters), and string is not empty,
                # keep the current value (or could clear/show error).
                # If string became empty due to deletion, it's handled by the 'if not value_str' above.
                if (
                    not value_str
                ):  # This case should ideally be caught by the initial check
                    self._current_value = 0
                # Silently pass on other ValueError, effectively ignoring invalid intermediate input
                pass

        self._update_display()  # Update all UI elements

    def _update_from_bits(self):
        # Callback when a bit checkbox is clicked
        if self._is_updating:  # Prevent recursion
            return

        new_value = 0
        # Reconstruct the integer value from the state of all bit checkboxes
        for i, var in enumerate(self.bit_vars):
            if var.get() == 1:
                new_value |= 1 << i  # Set the i-th bit

        self._current_value = new_value
        self._update_display()  # Update all UI elements

    def _update_display(self):
        # The central function to update all UI widgets based on _current_value
        self._is_updating = True  # Set flag to prevent recursive updates

        mask = self._get_mask()  # Get mask for the current number of bytes
        display_value = self._current_value & mask  # Apply mask
        num_bits = self.num_bytes_var.get() * 8

        # Update HEX, DEC, OCT, BIN entry fields
        self.hex_var.set(f"{display_value:X}")  # Format as uppercase hex

        if self.signed_mode_var.get():
            # Handle signed decimal representation
            if (display_value >> (num_bits - 1)) & 1:  # Check MSB for sign
                signed_val = display_value - (
                    1 << num_bits
                )  # Convert from two's complement
                self.dec_var.set(str(signed_val))
            else:
                self.dec_var.set(str(display_value))
        else:
            # Unsigned decimal representation
            self.dec_var.set(str(display_value))

        self.oct_var.set(f"{display_value:o}")  # Format as octal

        # Format as binary, ensuring "0" for zero value with zero bits
        self.bin_var.set(
            f"{display_value:b}" if num_bits > 0 or display_value > 0 else "0"
        )

        # Update bit checkboxes
        for i in range(64):
            is_active_bit = (
                i < num_bits
            )  # Check if the bit is within the current byte range
            cb = self.checkbox_widgets[i]

            if cb:  # Enable/disable checkbox based on active bit range
                if is_active_bit:
                    cb.state(["!disabled"])
                else:
                    cb.state(["disabled"])

            if is_active_bit:  # Set checkbox state if active
                if (display_value >> i) & 1:
                    self.bit_vars[i].set(1)
                else:
                    self.bit_vars[i].set(0)
            else:  # Clear checkbox if not active
                self.bit_vars[i].set(0)

        self._is_updating = False  # Clear update flag

    def _on_num_bytes_change(self, *args):
        # Callback when the number of bytes (selected by radio buttons) is changed
        new_mask = self._get_mask()
        self._current_value &= new_mask  # Mask the current value to the new bit width
        self._update_display()  # Update all UI elements

    def _set_status_message(self, message):
        # Sets the message in the status bar at the bottom of the window
        self.status_var.set(message)

    def _copy_to_clipboard(self, value_to_copy):
        # Copies the given string value to the system clipboard
        self.clipboard_clear()
        self.clipboard_append(value_to_copy)
        self._set_status_message(f"Copied to clipboard: {value_to_copy}")

    # --- Bitwise Operation Methods ---
    def _shift_left(self):
        # Performs a logical left shift
        amount = self.shift_amount_var.get()
        if amount < 0:  # Ignore negative shift amounts
            return
        mask = self._get_mask()
        self._current_value = (self._current_value << amount) & mask
        self._update_display()

    def _shift_right_logical(self):
        # Performs a logical right shift (fills with zeros)
        amount = self.shift_amount_var.get()
        if amount < 0:
            return
        mask = self._get_mask()
        self._current_value = (self._current_value >> amount) & mask
        self._update_display()

    def _shift_right_arithmetic(self):
        # Performs an arithmetic right shift (preserves sign bit)
        amount = self.shift_amount_var.get()
        if amount < 0:
            return
        num_bits = self.num_bytes_var.get() * 8
        mask = self._get_mask()

        if num_bits == 0:  # Handle zero bits case
            self._current_value = 0
            self._update_display()
            return

        msb_is_set = (self._current_value >> (num_bits - 1)) & 1  # Check the MSB

        val = self._current_value
        for _ in range(amount):  # Perform shift bit by bit to handle sign extension
            if msb_is_set:
                val = (val >> 1) | (1 << (num_bits - 1))  # Fill with MSB if set
            else:
                val = val >> 1  # Fill with 0
        self._current_value = val & mask
        self._update_display()

    def _rotate_left(self):
        # Performs a left rotation
        amount = self.shift_amount_var.get()
        if amount < 0:
            return
        num_bits = self.num_bytes_var.get() * 8
        if num_bits == 0:  # Cannot rotate with zero bits
            return

        mask = self._get_mask()
        amount %= num_bits  # Modulo to handle rotations larger than bit width

        val = self._current_value & mask
        # Bits shifted out from left are inserted on the right
        rotated = ((val << amount) | (val >> (num_bits - amount))) & mask
        self._current_value = rotated
        self._update_display()

    def _rotate_right(self):
        # Performs a right rotation
        amount = self.shift_amount_var.get()
        if amount < 0:
            return
        num_bits = self.num_bytes_var.get() * 8
        if num_bits == 0:
            return

        mask = self._get_mask()
        amount %= num_bits

        val = self._current_value & mask
        # Bits shifted out from right are inserted on the left
        rotated = ((val >> amount) | (val << (num_bits - amount))) & mask
        self._current_value = rotated
        self._update_display()

    def _invert_bits(self):
        # Inverts all bits within the selected byte range (bitwise NOT)
        mask = self._get_mask()
        self._current_value = (~self._current_value) & mask  # Apply NOT and then mask
        self._update_display()

    def _reverse_bits(self):
        # Reverses the order of bits within the selected byte range
        num_bits = self.num_bytes_var.get() * 8
        val = (
            self._current_value & self._get_mask()
        )  # Ensure we only reverse relevant bits
        reversed_val = 0
        for i in range(num_bits):
            if (val >> i) & 1:  # If i-th bit is set
                reversed_val |= 1 << (
                    num_bits - 1 - i
                )  # Set corresponding bit in reversed value
        self._current_value = reversed_val
        self._update_display()

    def _clear_bits(self):
        # Resets the current value to 0
        self._current_value = 0
        self._update_display()

    # --- Debugging Methods (not typically used in production UI) ---
    def _dump_bit_vars(self):
        # Debugging: Print the current state of bit_vars (checkbox states)
        print("bit_vars:", [var.get() for var in self.bit_vars])

    def _dump_current_value(self):
        # Debugging: Print the current internal value in all formats
        mask = self._get_mask()
        value = self._current_value & mask
        num_bits = self.num_bytes_var.get() * 8
        print(
            f"Current Value: {value} (HEX: {value:X}, DEC: {value}, OCT: {value:o}, BIN: {value:b})"
        )


# Main execution block
if __name__ == "__main__":
    app = BitCalc()  # Create an instance of the application
    app.mainloop()  # Start the Tkinter event loop
