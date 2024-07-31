def move_files_to_folders(labeled_flights):
    """Creates folders based on flight labels and moves files into respective folders."""
    for flight in labeled_flights:
        label = flight['Flight Label']
        folder_name = f"{label}_flights"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        file_name = flight.get('File Name')
        directory = flight.get('Directory')
        
        if file_name and directory:
            file_path = os.path.join(directory, file_name)
            destination_path = os.path.join(folder_name, file_name)
            
            shutil.move(file_path, destination_path)
        else:
            print(f"Warning: 'File Name' or 'Directory' key not found for flight: {flight}")