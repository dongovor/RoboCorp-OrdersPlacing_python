from robocorp.tasks import task
from RPA.HTTP import HTTP
from robocorp import browser 
from RPA.Tables import Tables
from RPA.PDF import PDF
import config
import time
import os
import zipfile


@task
def order_robots_from_RobotSpareBin():
    '''
    Order robots from RobotSpareBin.
    '''
    orders = get_orders()
    navigate_to_website()
    read_input_and_order_robots()
    compress_prepared_pdfs()
    cleanup_output_folder()

def get_orders():
    '''
    Get orders from RobotSpareBin.
    '''
    http = HTTP()
    http.download(config.INPUT_URL, overwrite=True, target_file='orders.csv')

def navigate_to_website():
    '''
    Navigate to RobotSpareBin website.
    '''
    browser.goto(config.URL)
    check_for_popup()

def check_for_popup():
    page = browser.page()
    try:
        page.wait_for_selector("xpath=//*[contains(@class, 'alert-buttons')]", timeout=1000)
        page.click("xpath=//*[contains(@class, 'btn btn-dark')]")
    except:
        print('No popup found')
    time.sleep(5)

def read_input_and_order_robots():
    '''
    Read input file and order robots.
    '''
    table = Tables()
    input_table = table.read_table_from_csv('orders.csv', header=True)
    for row in input_table:
        order_robot(row)
        check_for_popup()

def order_robot(robot):
    '''
    Order robot.
    '''
    page = browser.page()
    print(f'Ordering robot: Head > {robot["Head"]}, Body > {robot["Body"]}, Legs >{robot["Legs"]}, Address > {robot["Address"]}')
    page.select_option('#head', index=int(robot['Head']))
    page.click(f'#id-body-{str(robot["Body"])}')
    page.fill('input[placeholder="Enter the part number for the legs"]', str(robot['Legs']))
    page.fill('#address', str(robot['Address']))
    page.click('#order')
    # Check for alert and click order button
    while check_for_alert():
        page.click('#order')
    
    save_receipt_as_pdf()

    page.click('#order-another')
    
def check_for_alert():
    '''
    Check for alert when trying to order robot.
    '''
    page = browser.page()
    
    try:
        element = page.query_selector('.alert.alert-danger')
        if element:
            return True
        else:
            return False
    except:
        print('Failed to find alert')

def save_receipt_as_pdf():
    pdf = PDF()
    page = browser.page()

    # Get order number and prepare path to save
    element = page.query_selector('.badge.badge-success')
    order = element.inner_text()

    # Add placeholder for image
    order = f'{order}'

    path_to_save_robot = f'output/robot_{order}.png'
    path_to_save = f'output/{order}.pdf'
    print(f'Saving receipt as PDF to {path_to_save}')

    # Get order information and robot image
    receipt = page.locator('#receipt').inner_html()
    pdf.html_to_pdf(receipt, path_to_save)

    robot_image = page.query_selector('#robot-preview-image')
    robot_image.screenshot(path=path_to_save_robot)

    # Add image to PDF
    pdf.add_watermark_image_to_pdf(path_to_save_robot, path_to_save, path_to_save)

    os.remove(path_to_save_robot)

def order_another_robot():
    '''
    Click Order another robot.
    '''
    page = browser.page()
    page.click('#order-another')
    time.sleep(5)

def compress_prepared_pdfs():
    '''
    Compress prepared PDFs.
    '''
    zipf = zipfile.ZipFile('output/robot_orders.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('output/'):
        for file in files:
            if file.endswith('.pdf'):
                zipf.write(os.path.join(root, file))
    zipf.close()

def cleanup_output_folder():
    '''
    Remove all pdf files from output folder.
    '''
    for root, dirs, files in os.walk('output/'):
        for file in files:
            if file.endswith('.pdf'):
                os.remove(os.path.join(root, file))
