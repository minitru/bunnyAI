# Jessica's Crabby Editor - WordPress Integration Guide

This guide shows you how to integrate Jessica's Crabby Editor with your WordPress site.

## Method 1: Simple Shortcode (Quick Setup)

### Step 1: Add to functions.php
Add this code to your theme's `functions.php` file:

```php
function jessicas_crabby_editor_shortcode($atts) {
    $atts = shortcode_atts(array(
        'width' => '100%',
        'height' => '600px',
        'url' => 'http://your-server:7777' // Change this to your server URL
    ), $atts);
    
    $unique_id = 'crabby-editor-' . uniqid();
    
    ob_start();
    ?>
    <div id="<?php echo $unique_id; ?>" style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 20px 0;">
        <iframe 
            src="<?php echo esc_url($atts['url']); ?>" 
            width="100%" 
            height="100%" 
            frameborder="0"
            style="border: none;"
            title="Jessica's Crabby Editor - Literary Analysis">
        </iframe>
    </div>
    <?php
    return ob_get_clean();
}

add_shortcode('crabby_editor', 'jessicas_crabby_editor_shortcode');
```

### Step 2: Use the shortcode
In any post or page, add:
```
[crabby_editor]
```

Or with custom dimensions:
```
[crabby_editor width="800px" height="500px"]
```

## Method 2: Full WordPress Plugin

### Step 1: Create the plugin file
Create a new file: `/wp-content/plugins/jessicas-crabby-editor/jessicas-crabby-editor.php`

```php
<?php
/**
 * Plugin Name: Jessica's Crabby Editor
 * Description: Embed Jessica's Crabby Editor literary analysis interface
 * Version: 1.0
 * Author: Your Name
 */

if (!defined('ABSPATH')) {
    exit;
}

class JessicasCrabbyEditor {
    
    public function __construct() {
        add_action('init', array($this, 'init'));
        add_shortcode('crabby_editor', array($this, 'shortcode'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    public function init() {
        // Plugin initialization
    }
    
    public function shortcode($atts) {
        $options = get_option('crabby_editor_settings', array());
        $server_url = isset($options['server_url']) ? $options['server_url'] : 'http://localhost:7777';
        
        $atts = shortcode_atts(array(
            'width' => '100%',
            'height' => '600px',
            'url' => $server_url
        ), $atts);
        
        $unique_id = 'crabby-editor-' . uniqid();
        
        ob_start();
        ?>
        <div id="<?php echo $unique_id; ?>" class="crabby-editor-container" style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <iframe 
                src="<?php echo esc_url($atts['url']); ?>" 
                width="100%" 
                height="100%" 
                frameborder="0"
                style="border: none;"
                title="Jessica's Crabby Editor - Literary Analysis">
            </iframe>
        </div>
        <?php
        return ob_get_clean();
    }
    
    public function add_admin_menu() {
        add_options_page(
            'Jessica\'s Crabby Editor Settings',
            'Crabby Editor',
            'manage_options',
            'crabby-editor-settings',
            array($this, 'admin_page')
        );
    }
    
    public function register_settings() {
        register_setting('crabby_editor_settings_group', 'crabby_editor_settings');
    }
    
    public function admin_page() {
        if (isset($_POST['submit'])) {
            update_option('crabby_editor_settings', array(
                'server_url' => sanitize_url($_POST['server_url'])
            ));
            echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
        }
        
        $options = get_option('crabby_editor_settings', array());
        $server_url = isset($options['server_url']) ? $options['server_url'] : 'http://localhost:7777';
        ?>
        <div class="wrap">
            <h1>📝 Jessica's Crabby Editor Settings</h1>
            <form method="post" action="">
                <?php settings_fields('crabby_editor_settings_group'); ?>
                <table class="form-table">
                    <tr>
                        <th scope="row">Server URL</th>
                        <td>
                            <input type="url" name="server_url" value="<?php echo esc_attr($server_url); ?>" class="regular-text" />
                            <p class="description">The URL where your Jessica's Crabby Editor server is running (e.g., http://your-server:7777)</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            
            <h2>Usage Instructions</h2>
            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Basic Usage:</h3>
                <p>Add this shortcode to any post or page:</p>
                <code>[crabby_editor]</code>
                
                <h3>Custom Dimensions:</h3>
                <p>Specify custom width and height:</p>
                <code>[crabby_editor width="800px" height="500px"]</code>
                
                <h3>Custom Server URL:</h3>
                <p>Override the default server URL:</p>
                <code>[crabby_editor url="http://your-custom-server:7777"]</code>
            </div>
            
            <h2>Features</h2>
            <ul>
                <li>✅ Literary analysis and editing</li>
                <li>✅ Book selection (All Books, No Name Key, Sidetrack Key)</li>
                <li>✅ Comprehensive writing feedback</li>
                <li>✅ Line editing capabilities</li>
                <li>✅ Responsive design</li>
            </ul>
        </div>
        <?php
    }
}

new JessicasCrabbyEditor();
?>
```

### Step 2: Activate the plugin
1. Go to WordPress Admin → Plugins
2. Find "Jessica's Crabby Editor" and click "Activate"
3. Go to Settings → Crabby Editor to configure

## Method 3: Gutenberg Block

### Create a custom Gutenberg block
Add this to your theme or create a plugin:

```php
function register_crabby_editor_block() {
    wp_register_script(
        'crabby-editor-block',
        get_template_directory_uri() . '/js/crabby-editor-block.js',
        array('wp-blocks', 'wp-element', 'wp-editor')
    );
    
    register_block_type('crabby-editor/editor', array(
        'editor_script' => 'crabby-editor-block',
        'render_callback' => 'render_crabby_editor_block'
    ));
}
add_action('init', 'register_crabby_editor_block');

function render_crabby_editor_block($attributes) {
    $server_url = isset($attributes['serverUrl']) ? $attributes['serverUrl'] : 'http://localhost:7777';
    $width = isset($attributes['width']) ? $attributes['width'] : '100%';
    $height = isset($attributes['height']) ? $attributes['height'] : '600px';
    
    $unique_id = 'crabby-editor-' . uniqid();
    
    ob_start();
    ?>
    <div id="<?php echo $unique_id; ?>" style="width: <?php echo esc_attr($width); ?>; height: <?php echo esc_attr($height); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 20px 0;">
        <iframe 
            src="<?php echo esc_url($server_url); ?>" 
            width="100%" 
            height="100%" 
            frameborder="0"
            style="border: none;"
            title="Jessica's Crabby Editor">
        </iframe>
    </div>
    <?php
    return ob_get_clean();
}
```

## Method 4: Widget

### Add as a sidebar widget
```php
class CrabbyEditorWidget extends WP_Widget {
    
    public function __construct() {
        parent::__construct(
            'crabby_editor_widget',
            'Jessica\'s Crabby Editor',
            array('description' => 'Embed Jessica\'s Crabby Editor in your sidebar')
        );
    }
    
    public function widget($args, $instance) {
        $server_url = isset($instance['server_url']) ? $instance['server_url'] : 'http://localhost:7777';
        $height = isset($instance['height']) ? $instance['height'] : '400px';
        
        echo $args['before_widget'];
        echo $args['before_title'] . '📝 Literary Editor' . $args['after_title'];
        
        $unique_id = 'crabby-editor-widget-' . uniqid();
        ?>
        <div id="<?php echo $unique_id; ?>" style="width: 100%; height: <?php echo esc_attr($height); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
            <iframe 
                src="<?php echo esc_url($server_url); ?>" 
                width="100%" 
                height="100%" 
                frameborder="0"
                style="border: none;"
                title="Jessica's Crabby Editor">
            </iframe>
        </div>
        <?php
        echo $args['after_widget'];
    }
    
    public function form($instance) {
        $server_url = isset($instance['server_url']) ? $instance['server_url'] : 'http://localhost:7777';
        $height = isset($instance['height']) ? $instance['height'] : '400px';
        ?>
        <p>
            <label for="<?php echo $this->get_field_id('server_url'); ?>">Server URL:</label>
            <input class="widefat" id="<?php echo $this->get_field_id('server_url'); ?>" name="<?php echo $this->get_field_name('server_url'); ?>" type="url" value="<?php echo esc_attr($server_url); ?>" />
        </p>
        <p>
            <label for="<?php echo $this->get_field_id('height'); ?>">Height:</label>
            <input class="widefat" id="<?php echo $this->get_field_id('height'); ?>" name="<?php echo $this->get_field_name('height'); ?>" type="text" value="<?php echo esc_attr($height); ?>" />
        </p>
        <?php
    }
    
    public function update($new_instance, $old_instance) {
        $instance = array();
        $instance['server_url'] = sanitize_url($new_instance['server_url']);
        $instance['height'] = sanitize_text_field($new_instance['height']);
        return $instance;
    }
}

function register_crabby_editor_widget() {
    register_widget('CrabbyEditorWidget');
}
add_action('widgets_init', 'register_crabby_editor_widget');
```

## Server Configuration

### Make sure your server is accessible
1. **Update server URL** in WordPress settings to match your actual server
2. **Configure firewall** to allow access to port 7777
3. **Use HTTPS** for production sites
4. **Set up domain** instead of IP address for better reliability

### Example server URLs:
- Local development: `http://localhost:7777`
- Local network: `http://192.168.1.100:7777`
- Production: `https://your-domain.com:7777`
- Cloud server: `https://your-server.com:7777`

## Security Considerations

1. **HTTPS**: Use SSL certificates for production
2. **Authentication**: Consider adding basic auth to your server
3. **CORS**: Configure CORS headers if needed
4. **Firewall**: Restrict access to your server
5. **Updates**: Keep your server and WordPress updated

## Troubleshooting

### Common Issues:
1. **Iframe not loading**: Check server URL and firewall settings
2. **Mixed content errors**: Use HTTPS for both WordPress and server
3. **Size issues**: Adjust width/height parameters
4. **Server not responding**: Check if the Python server is running

### Testing:
1. Test the server URL directly in your browser
2. Check WordPress error logs
3. Verify shortcode syntax
4. Test with different browsers

## Recommended Setup

For production, I recommend:
1. **Use Method 2 (Full Plugin)** for better management
2. **Set up HTTPS** for security
3. **Use a dedicated domain** for your server
4. **Configure proper firewall rules**
5. **Set up monitoring** for your server

This gives you a professional, integrated literary analysis tool right in your WordPress site!
