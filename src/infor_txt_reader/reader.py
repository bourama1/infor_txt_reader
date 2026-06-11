import re


class InforReader:
    """
    Reader for Infor BOM text files.

    Groups configuration options by 'Manufactured Item' (order/position)
    and handles parent/child section relationships.
    """

    def __init__(self):
        # Patterns for metadata extraction
        self.date_re = re.compile(r"Date\s*:\s*([^\[]+)")
        self.manufactured_item_re = re.compile(
            r"Manufactured Item\s*:\s*([A-Z0-9]+)-(\d+)(?:.*/(\d+))?"
        )
        self.special_item_re = re.compile(r"Manufactured Item\s*:\s*([A-Z0-9]+)/(\d+)")

        # Patterns for configuration blocks
        self.block_start_re = re.compile(
            r"\|\s*Prod\. Var\. Options for Item", re.IGNORECASE
        )
        self.name_line_re = re.compile(r"\|\s*(.*?)\s+Option Set", re.IGNORECASE)
        self.section_name_re = re.compile(r"^\d+\..*section", re.IGNORECASE)

        # Pattern for feature lines: | Code | Desc | Value | ...
        self.feature_re = re.compile(
            r"\|\s*([A-Z0-9]+)\s*\|\s*[^|]+\s*\|\s*([^|]+)\s*\|"
        )

    def read(self, file_path: str) -> list[dict]:
        """
        Parses the Infor text file and returns a list of configurations.

        Each configuration is a dictionary with a 'meta' key and multiple
        section keys containing characteristic codes and values.
        """
        results = []
        result_map = {}
        current_config = None
        current_header = None
        current_parent = None
        expecting_name = False
        global_date = None
        variant_to_pos = {}

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # --- Metadata (Date) ---
                if "Date" in line and "Page" in line:
                    match = self.date_re.search(line)
                    if match:
                        global_date = match.group(1).strip()
                        if current_config:
                            current_config["meta"]["product_configuration_date"] = (
                                global_date
                            )

                # --- Manufactured Item Identification ---
                if "Manufactured Item" in line:
                    match = self.manufactured_item_re.search(line)
                    if match:
                        order = match.group(1).strip()
                        pos = match.group(2).strip()
                        variant = match.group(3)
                        if variant:
                            variant_to_pos[variant.strip()] = pos

                        key = (order, pos)
                        if key not in result_map:
                            new_config = {"meta": {}}
                            if global_date:
                                new_config["meta"]["product_configuration_date"] = (
                                    global_date
                                )
                            result_map[key] = new_config
                            results.append(new_config)
                        current_config = result_map[key]
                        current_config["meta"]["reference_order"] = order
                        current_config["meta"]["reference_position"] = pos

                        # Reset block state for new item component
                        current_header = None
                        current_parent = None
                        expecting_name = False
                    else:
                        # Try special format: TQ1000514T10LN/211017
                        match = self.special_item_re.search(line)
                        if match:
                            prefix, variant = match.groups()
                            variant = variant.strip()
                            order = prefix[:9]  # Assume order is first 9 chars
                            pos = variant_to_pos.get(variant)

                            if pos:
                                key = (order, pos)
                                if key not in result_map:
                                    new_config = {"meta": {}}
                                    if global_date:
                                        new_config["meta"][
                                            "product_configuration_date"
                                        ] = global_date
                                    result_map[key] = new_config
                                    results.append(new_config)
                                current_config = result_map[key]
                                current_config["meta"]["reference_order"] = order
                                current_config["meta"]["reference_position"] = pos
                            else:
                                current_config = None
                        else:
                            # If Manufactured Item found but doesn't match regex,
                            # stop associating with the current config.
                            current_config = None

                if not current_config:
                    continue

                # --- Detection of configuration blocks ---
                if self.block_start_re.search(line):
                    expecting_name = True
                    continue

                # --- Header Name Extraction & Parent Logic ---
                if expecting_name:
                    match = self.name_line_re.search(line)
                    if match:
                        raw_name = match.group(1).strip()

                        # Check if this name is a "Parent Section" (e.g., "5. FVE section")
                        if self.section_name_re.search(raw_name):
                            current_parent = raw_name
                            current_header = raw_name
                        else:
                            # Inherit parent number if applicable
                            if current_parent and "FVE" in current_parent:
                                parent_num = current_parent.split(".")[0]
                                current_header = f"{parent_num}. {raw_name}"
                            else:
                                current_header = raw_name

                        if current_header not in current_config:
                            current_config[current_header] = {}

                    expecting_name = False
                    continue

                # --- Feature line parsing ---
                if current_header and line.startswith("|"):
                    match = self.feature_re.search(line)
                    if match:
                        code, value = match.groups()
                        code = code.strip()
                        value = value.strip()

                        if code and code != "Product Feature":
                            current_config[current_header][code] = value

        return results
