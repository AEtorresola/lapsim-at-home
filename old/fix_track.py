
import csv
import os

def fix_turns(input_csv_path, output_csv_path):
    """
    Reads a CSV file, inserts "Straight,0.01,0" rows between consecutive
    left/right turns, and writes the result to a new CSV file.

    Args:
        input_csv_path (str): Path to the input CSV file.
        output_csv_path (str): Path to the output CSV file.
    """

    rows = []
    with open(input_csv_path, 'r') as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    fixed_rows = []
    i = 0
    while i < len(rows):
        fixed_rows.append(rows[i])
        if i < len(rows) - 1:
            current_direction = rows[i][0].strip().lower()
            next_direction = rows[i + 1][0].strip().lower()

            if current_direction in ('left', 'right') and \
               next_direction in ('left', 'right'):
                fixed_rows.append(['Straight', '0.01', '0'])
        i += 1

    with open(output_csv_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(fixed_rows)


if __name__ == "__main__":
    tracks_directory = "tracks"
    input_file = '2021_michigan.csv'  # Replace with your input file name
    input_path = os.path.join(tracks_directory, input_file)
    output_file = 'fixed_' + input_file
    output_path = os.path.join(tracks_directory, output_file)

    # Ensure the "tracks" directory exists
    if not os.path.exists(tracks_directory):
        os.makedirs(tracks_directory)

    fix_turns(input_path, output_path)
    print(f"Fixed CSV saved to: {output_path}")


