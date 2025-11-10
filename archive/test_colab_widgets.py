"""
Quick test to verify this works in Colab's ipywidgets environment
Run this in a Colab cell to test widget rendering
"""

# Test 1: Check if we're in Colab
import sys
IN_COLAB = 'google.colab' in sys.modules
print(f"Running in Colab: {IN_COLAB}")

# Test 2: Import ipywidgets
try:
    import ipywidgets as widgets
    from IPython.display import display, HTML
    print("✅ ipywidgets imported successfully")
except ImportError as e:
    print(f"❌ ipywidgets import failed: {e}")
    sys.exit(1)

# Test 3: Enable custom widget manager (Colab requirement)
if IN_COLAB:
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
        print("✅ Custom widget manager enabled")
    except Exception as e:
        print(f"⚠️ Widget manager: {e}")

# Test 4: Create and display test widgets
print("\n🧪 Testing widget rendering...")

test_button = widgets.Button(
    description='Test Button',
    button_style='success',
    icon='check'
)

test_progress = widgets.FloatProgress(
    value=50,
    min=0,
    max=100,
    description='Progress:',
    bar_style='info'
)

test_text = widgets.Textarea(
    value='Test textarea',
    placeholder='Type here',
    description='Input:',
)

test_dropdown = widgets.Dropdown(
    options=['Option 1', 'Option 2', 'Option 3'],
    value='Option 1',
    description='Select:',
)

test_html = widgets.HTML('<h3 style="color: #1a73e8;">✅ Widgets Working!</h3>')

# Display all widgets
test_ui = widgets.VBox([
    test_html,
    test_button,
    test_progress,
    test_text,
    test_dropdown,
    widgets.HTML('<p>If you can see and interact with these widgets, the GUI will work!</p>')
])

display(test_ui)

print("\n✅ If you see widgets above, the main GUI will work perfectly!")
print("📝 To run the main app: !python torrent_colab_optimized.py")
