#TODO : remove the files for all libraries and all such as __ ones

import os

def dump_all_files_separately(root_dir: str, output_dir: str = "output_utility"):
    """
    Recursively walk root_dir, and for every file found:
    - Create a separate text file inside output_dir.
    - Write:

      original_filename.ext:

      <file contents>
      **********
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in sorted(filenames):
            # Full path of source file
            src_path = os.path.join(dirpath, fname)

            # Read file contents with a safe encoding strategy
            try:
                with open(src_path, "r", encoding="utf-8") as src_f:
                    content = src_f.read()
            except UnicodeDecodeError:
                # Fallback if UTF-8 fails
                try:
                    with open(src_path, "r", encoding="latin-1") as src_f:
                        content = src_f.read()
                except Exception as e:
                    print(f"Skipping (cannot decode): {src_path} ({e})")
                    continue
            except Exception as e:
                print(f"Skipping (cannot open): {src_path} ({e})")
                continue

            # Create a safe output filename based on relative path
            rel_path = os.path.relpath(src_path, root_dir)
            rel_path_sanitized = rel_path.replace(os.sep, "__")

            # Example: a.py → a.py_dump.txt, sub/dir/x.html → sub__dir__x.html_dump.txt
            out_name = f"{rel_path_sanitized}_dump.txt"
            out_path = os.path.join(output_dir, out_name)

            with open(out_path, "w", encoding="utf-8") as out_f:
                out_f.write(f"{fname}:\n\n")
                out_f.write(content.rstrip() + "\n")
                out_f.write("\n**********\n")

            print(f"Wrote: {out_path}")

    print(f"\nDone. All files from '{root_dir}' have been dumped into '{output_dir}'.")


if __name__ == "__main__":
    parent_folder = input("Enter the full path of the parent folder: ").strip()

    if not os.path.isdir(parent_folder):
        print(f"Error: '{parent_folder}' is not a valid directory.")
    else:
        dump_all_files_separately(parent_folder)
