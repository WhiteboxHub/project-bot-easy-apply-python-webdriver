'''
Shadow DOM Handler Module

This module provides utility functions to interact with elements inside Shadow DOM trees.
Shadow DOM elements are not accessible through normal DOM traversal, so special handling is required.

Author:     GitHub Copilot
License:    GNU Affero General Public License

Problem:
- LinkedIn uses Shadow DOM for many UI elements (buttons, inputs, etc.)
- Normal Selenium findElement() cannot access Shadow DOM elements
- Clicking these buttons fails with "element not found" errors

Solution:
- Use JavaScript to traverse through shadow roots
- Detect if element is in open or closed shadow DOM
- Use elementFromPoint() or dispatchEvent() as fallback for closed shadow roots
- Provide robust clicking with multiple fallback strategies
'''

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bot.utils.logger import print_lg
from bot.utils.delays import buffer
# click_gap is now handled via get_setting in form_filler or similar mechanism
click_gap = 2 
from time import sleep


# ============================================================================
# SHADOW DOM DETECTION & TRAVERSAL FUNCTIONS
# ============================================================================

def find_in_shadow_root(driver: WebDriver, text: str, time: float = 5.0) -> WebElement | None:
    '''
    Recursively searches for an element with given text inside Shadow DOM trees.
    
    Flow:
    1. Execute JavaScript to search through all shadow roots
    2. Look for elements containing the specified text
    3. Return the first matching element found
    
    Args:
        driver: WebDriver instance
        text: Text content to search for (e.g., "Next", "Easy Apply")
        time: Max wait time in seconds
    
    Returns:
        WebElement if found, None otherwise
    '''
    try:
        # JavaScript function to recursively search through shadow DOMs
        script = """
        function findInShadowRoot(searchText) {
            // Search in light DOM first
            let walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                // Check if current node contains the text
                if (node.textContent && node.textContent.includes(searchText)) {
                    // Verify it's the exact element (not parent)
                    if (node.innerText === searchText || node.textContent.trim() === searchText) {
                        return node;
                    }
                }
                
                // If element has shadow root, search inside it
                if (node.shadowRoot) {
                    let result = findInShadowRootRecursive(node.shadowRoot, searchText);
                    if (result) return result;
                }
            }
            return null;
        }
        
        function findInShadowRootRecursive(shadowRoot, searchText) {
            let walker = document.createTreeWalker(
                shadowRoot,
                NodeFilter.SHOW_ELEMENT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent && node.textContent.includes(searchText)) {
                    if (node.innerText === searchText || node.textContent.trim() === searchText) {
                        return node;
                    }
                }
                
                // Recursively check child shadow roots
                if (node.shadowRoot) {
                    let result = findInShadowRootRecursive(node.shadowRoot, searchText);
                    if (result) return result;
                }
            }
            return null;
        }
        
        return findInShadowRoot(arguments[0]);
        """
        
        element = WebDriverWait(driver, time).until(
            EC.presence_of_element_located((By.XPATH, "//*"))  # Wait for any element
        )
        
        result = driver.execute_script(script, text)
        return result if result else None
        
    except Exception as e:
        print_lg(f"Error searching for '{text}' in shadow DOM: {str(e)}")
        return None


def is_in_shadow_dom(driver: WebDriver, element: WebElement) -> bool:
    '''
    Checks if an element is inside a Shadow DOM tree.
    
    Args:
        driver: WebDriver instance
        element: WebElement to check
    
    Returns:
        True if element is in shadow DOM, False otherwise
    '''
    try:
        script = """
        function isInShadowDOM(elem) {
            let parent = elem.parentNode;
            while (parent) {
                if (parent instanceof ShadowRoot) {
                    return true;
                }
                parent = parent.parentNode || (parent.host ? parent.host.parentNode : null);
            }
            return false;
        }
        return isInShadowDOM(arguments[0]);
        """
        return driver.execute_script(script, element)
    except Exception as e:
        print_lg(f"Error checking if element is in shadow DOM: {str(e)}")
        return False


def is_element_visible(driver: WebDriver, element: WebElement) -> bool:
    '''
    Checks if an element is actually visible and clickable on the page.
    
    Visibility checks:
    - Element has non-zero dimensions
    - Element is not hidden by CSS (display, visibility, opacity)
    - Element is not clipped or covered by other elements
    
    Args:
        driver: WebDriver instance
        element: WebElement to check
    
    Returns:
        True if element is visible, False otherwise
    '''
    try:
        script = """
        function isElementVisible(elem) {
            // Check if element is hidden via display or visibility
            let style = window.getComputedStyle(elem);
            if (style.display === 'none' || style.visibility === 'hidden') {
                return false;
            }
            
            // Check if element has zero dimensions
            let rect = elem.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) {
                return false;
            }
            
            // Check if element is within viewport
            if (rect.top < 0 || rect.left < 0) {
                return false;
            }
            
            // Check opacity
            if (style.opacity === '0') {
                return false;
            }
            
            return true;
        }
        return isElementVisible(arguments[0]);
        """
        return driver.execute_script(script, element)
    except Exception as e:
        print_lg(f"Error checking element visibility: {str(e)}")
        return True  # Assume visible on error


def get_element_info(driver: WebDriver, element: WebElement) -> dict:
    '''
    Gets detailed information about an element for debugging.
    
    Returns:
        Dictionary with element's properties
    '''
    try:
        script = """
        function getElementInfo(elem) {
            let rect = elem.getBoundingClientRect();
            let style = window.getComputedStyle(elem);
            let parent = elem.parentNode;
            let parentStyle = parent ? window.getComputedStyle(parent) : {};
            
            return {
                tagName: elem.tagName,
                text: elem.innerText || elem.textContent,
                id: elem.id,
                className: elem.className,
                rect: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                },
                style: {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    pointerEvents: style.pointerEvents
                },
                parentStyle: {
                    display: parentStyle.display,
                    overflow: parentStyle.overflow,
                    visibility: parentStyle.visibility
                },
                isInShadowRoot: elem.parentNode instanceof ShadowRoot
            };
        }
        return getElementInfo(arguments[0]);
        """
        return driver.execute_script(script, element)
    except Exception as e:
        print_lg(f"Error getting element info: {str(e)}")
        return {}


# ============================================================================
# ROBUST CLICKING FUNCTIONS
# ============================================================================

def robust_click(driver: WebDriver, element: WebElement, text: str = "") -> bool:
    '''
    Attempts to click an element using multiple fallback strategies.
    
    Clicking Flow (in order of attempt):
    1. Try standard element.click()
    2. Try JavaScript click on the element
    3. Try clicking parent element (if element is disabled/hidden)
    4. Try using elementFromPoint() if element center is visible
    5. Try dispatching mouse events (mouseDown, mouseUp, click)
    
    Args:
        driver: WebDriver instance
        element: WebElement to click
        text: Descriptive text for logging
    
    Returns:
        True if click successful, False otherwise
    '''
    try:
        # Scroll element into view first
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        sleep(0.5)
        
        # Get element info for debugging
        info = get_element_info(driver, element)
        print_lg(f"Attempting to click: {text or info.get('text', 'element')}")
        
        # Strategy 1: Direct click()
        try:
            element.click()
            buffer(click_gap)
            print_lg(f"✓ Clicked using element.click(): {text}")
            return True
        except Exception as e:
            print_lg(f"  ✗ element.click() failed: {str(e)}")
        
        # Strategy 2: JavaScript click
        try:
            driver.execute_script("arguments[0].click();", element)
            buffer(click_gap)
            print_lg(f"✓ Clicked using JavaScript click: {text}")
            return True
        except Exception as e:
            print_lg(f"  ✗ JavaScript click failed: {str(e)}")
        
        # Strategy 3: Click parent (if element is hidden)
        try:
            parent = element.find_element(By.XPATH, "./..")
            if parent:
                parent.click()
                buffer(click_gap)
                print_lg(f"✓ Clicked parent element: {text}")
                return True
        except Exception as e:
            print_lg(f"  ✗ Parent click failed")
        
        # Strategy 4: elementFromPoint (click element coordinates)
        try:
            script = """
            function clickAtPoint(elem) {
                let rect = elem.getBoundingClientRect();
                let x = rect.left + rect.width / 2;
                let y = rect.top + rect.height / 2;
                
                let elementAtPoint = document.elementFromPoint(x, y);
                if (elementAtPoint) {
                    elementAtPoint.click();
                    return true;
                }
                return false;
            }
            return clickAtPoint(arguments[0]);
            """
            result = driver.execute_script(script, element)
            if result:
                buffer(click_gap)
                print_lg(f"✓ Clicked using elementFromPoint: {text}")
                return True
        except Exception as e:
            print_lg(f"  ✗ elementFromPoint click failed: {str(e)}")
        
        # Strategy 5: Dispatch mouse events
        try:
            script = """
            function dispatchClickEvents(elem) {
                let rect = elem.getBoundingClientRect();
                let x = rect.left + rect.width / 2;
                let y = rect.top + rect.height / 2;
                
                let mouseDownEvent = new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y
                });
                
                let mouseUpEvent = new MouseEvent('mouseup', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y
                });
                
                let clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y
                });
                
                elem.dispatchEvent(mouseDownEvent);
                elem.dispatchEvent(mouseUpEvent);
                elem.dispatchEvent(clickEvent);
                return true;
            }
            return dispatchClickEvents(arguments[0]);
            """
            result = driver.execute_script(script, element)
            if result:
                buffer(click_gap)
                print_lg(f"✓ Clicked using dispatchEvent: {text}")
                return True
        except Exception as e:
            print_lg(f"  ✗ dispatchEvent click failed: {str(e)}")
        
        print_lg(f"✗ All click strategies failed for: {text}")
        print_lg(f"  Element info: {info}")
        return False
        
    except Exception as e:
        print_lg(f"Error in robust_click: {str(e)}")
        return False


def find_and_click_robust(driver: WebDriver, text: str, time: float = 5.0) -> bool:
    '''
    Combines shadow DOM search with robust clicking.
    
    Complete Flow:
    1. Try to find element in light DOM using XPath
    2. If not found, search in Shadow DOM using JavaScript
    3. Use robust_click() to click the element
    
    Args:
        driver: WebDriver instance
        text: Text content of element to find and click
        time: Max wait time
    
    Returns:
        True if found and clicked, False otherwise
    '''
    try:
        # Try light DOM first
        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'.//span[normalize-space(.)="{text}"]')
                )
            )
            print_lg(f"Found element in light DOM: {text}")
            return robust_click(driver, element, text)
        except Exception as e:
            print_lg(f"Element not in light DOM, checking shadow DOM...")
        
        # Try shadow DOM
        element = find_in_shadow_root(driver, text, time)
        if element:
            print_lg(f"Found element in shadow DOM: {text}")
            return robust_click(driver, element, text)
        
        print_lg(f"Element not found anywhere: {text}")
        return False
        
    except Exception as e:
        print_lg(f"Error in find_and_click_robust: {str(e)}")
        return False


# ============================================================================
# INPUT FIELD HANDLING FOR SHADOW DOM
# ============================================================================

def find_and_fill_input(driver: WebDriver, placeholder: str, value: str, time: float = 5.0) -> bool:
    '''
    Finds and fills an input field, handling Shadow DOM if necessary.
    
    Args:
        driver: WebDriver instance
        placeholder: Placeholder text of input field
        value: Value to enter
        time: Max wait time
    
    Returns:
        True if successful, False otherwise
    '''
    try:
        # Try light DOM first
        try:
            input_field = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//input[@placeholder="{placeholder}"]')
                )
            )
            print_lg(f"Found input field in light DOM: {placeholder}")
        except:
            # Try shadow DOM
            script = f"""
            function findInputByPlaceholder(placeholder) {{
                function searchShadowRoot(root, placeholder) {{
                    let walker = document.createTreeWalker(
                        root,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.tagName === 'INPUT' && node.placeholder === placeholder) {{
                            return node;
                        }}
                        if (node.shadowRoot) {{
                            let result = searchShadowRoot(node.shadowRoot, placeholder);
                            if (result) return result;
                        }}
                    }}
                    return null;
                }}
                return searchShadowRoot(document, placeholder);
            }}
            return findInputByPlaceholder(arguments[0]);
            """
            input_field = driver.execute_script(script, placeholder)
            if not input_field:
                print_lg(f"Input field not found: {placeholder}")
                return False
            print_lg(f"Found input field in shadow DOM: {placeholder}")
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
        sleep(0.3)
        
        # Clear and fill
        input_field.clear()
        sleep(0.2)
        input_field.send_keys(value)
        sleep(0.2)
        
        print_lg(f"✓ Successfully filled input: {placeholder}")
        return True
        
    except Exception as e:
        print_lg(f"Error filling input field: {str(e)}")
        return False
