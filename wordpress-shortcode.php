<?php
// WordPress Shortcode for Jessica's Crabby Editor
// Add this to your theme's functions.php or create a plugin

function jessicas_crabby_editor_shortcode($atts) {
    // Default attributes
    $atts = shortcode_atts(array(
        'width' => '100%',
        'height' => '600px',
        'url' => 'http://your-server:7777' // Change this to your server URL
    ), $atts);
    
    // Generate unique ID for this instance
    $unique_id = 'crabby-editor-' . uniqid();
    
    ob_start();
    ?>
    <div id="<?php echo $unique_id; ?>" style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
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

// Register the shortcode
add_shortcode('crabby_editor', 'jessicas_crabby_editor_shortcode');

// Usage: [crabby_editor width="800px" height="500px" url="http://your-server:7777"]
?>
