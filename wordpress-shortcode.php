<?php
// WordPress Shortcode for Bunny AI
// Add this to your theme's functions.php or create a plugin

function bunny_ai_shortcode($atts) {
    // Default attributes
    $atts = shortcode_atts(array(
        'width' => '100%',
        'height' => '600px',
        'url' => 'http://your-server:7777' // Change this to your server URL
    ), $atts);
    
    // Generate unique ID for this instance
    $unique_id = 'bunny-ai-' . uniqid();
    
    ob_start();
    ?>
    <div id="<?php echo $unique_id; ?>" style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
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

// Register the shortcode
add_shortcode('bunny_ai', 'bunny_ai_shortcode');

// Usage: [bunny_ai width="800px" height="500px" url="http://your-server:7777"]
?>
