<?php
/**
 * Plugin Name: Bunny AI Chat
 * Description: Embed Bunny AI chat interface in WordPress
 * Version: 1.0
 * Author: Your Name
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class BunnyAIPlugin {
    
    public function __construct() {
        add_action('init', array($this, 'init'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_shortcode('bunny_ai', array($this, 'bunny_ai_shortcode'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
    }
    
    public function init() {
        // Plugin initialization
    }
    
    public function enqueue_scripts() {
        // Add any custom CSS/JS if needed
    }
    
    public function bunny_ai_shortcode($atts) {
        $options = get_option('bunny_ai_settings', array());
        $server_url = isset($options['server_url']) ? $options['server_url'] : 'http://localhost:7777';
        
        $atts = shortcode_atts(array(
            'width' => '100%',
            'height' => '600px',
            'url' => $server_url
        ), $atts);
        
        $unique_id = 'bunny-ai-' . uniqid();
        
        ob_start();
        ?>
        <div id="<?php echo $unique_id; ?>" class="bunny-ai-container" style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 20px 0;">
            <iframe 
                src="<?php echo esc_url($atts['url']); ?>" 
                width="100%" 
                height="100%" 
                frameborder="0"
                style="border: none;"
                title="Bunny AI Chat Interface">
            </iframe>
        </div>
        <?php
        return ob_get_clean();
    }
    
    public function add_admin_menu() {
        add_options_page(
            'Bunny AI Settings',
            'Bunny AI',
            'manage_options',
            'bunny-ai-settings',
            array($this, 'admin_page')
        );
    }
    
    public function admin_page() {
        if (isset($_POST['submit'])) {
            update_option('bunny_ai_settings', array(
                'server_url' => sanitize_url($_POST['server_url'])
            ));
            echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
        }
        
        $options = get_option('bunny_ai_settings', array());
        $server_url = isset($options['server_url']) ? $options['server_url'] : 'http://localhost:7777';
        ?>
        <div class="wrap">
            <h1>Bunny AI Settings</h1>
            <form method="post" action="">
                <table class="form-table">
                    <tr>
                        <th scope="row">Server URL</th>
                        <td>
                            <input type="url" name="server_url" value="<?php echo esc_attr($server_url); ?>" class="regular-text" />
                            <p class="description">The URL where your Bunny AI server is running (e.g., http://your-server:7777)</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            
            <h2>Usage</h2>
            <p>Use the shortcode <code>[bunny_ai]</code> in your posts or pages.</p>
            <p>You can customize the size: <code>[bunny_ai width="800px" height="500px"]</code></p>
        </div>
        <?php
    }
}

// Initialize the plugin
new BunnyAIPlugin();
?>
