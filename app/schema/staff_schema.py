def individual_serial(staff) -> dict:
    return {
            "staff_id" : str(staff["_id"]),
            "name" : staff["name"],
            "email" : staff["email"],
        }
        

def staff_list(staffs) -> list:
    return [individual_serial(staff) for staff in staffs]