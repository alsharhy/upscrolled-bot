<?php
/********************
 * الإعدادات
 ********************/
$facebookPage = "https://mbasic.facebook.com/AlArabiya";
$telegramBotToken = "PUT_BOT_TOKEN_HERE";
$telegramChatId   = "PUT_CHAT_ID_HERE";

$hashFile = __DIR__ . "/last_post_hash.txt";

/********************
 * دوال مساعدة
 ********************/
function fetchPage($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_USERAGENT => "Mozilla/5.0",
        CURLOPT_TIMEOUT => 20
    ]);
    $html = curl_exec($ch);
    curl_close($ch);
    return $html;
}

function sendTelegram($token, $chatId, $message) {
    $url = "https://api.telegram.org/bot{$token}/sendMessage";
    $data = [
        "chat_id" => $chatId,
        "text" => $message,
        "disable_web_page_preview" => false
    ];
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $data,
        CURLOPT_RETURNTRANSFER => true
    ]);
    curl_exec($ch);
    curl_close($ch);
}

function getLastHash($file) {
    return file_exists($file) ? trim(file_get_contents($file)) : "";
}

function saveHash($file, $hash) {
    file_put_contents($file, $hash);
}

/********************
 * جلب آخر منشور
 ********************/
$html = fetchPage($facebookPage);

if (!$html) {
    sendTelegram($telegramBotToken, $telegramChatId, "⚠️ فشل جلب صفحة فيسبوك");
    exit;
}

/*
 نبحث عن أول رابط منشور
 mbasic يعرض الروابط بهذا الشكل تقريبًا:
 /story.php?story_fbid=XXXX&id=YYYY
*/
if (!preg_match('/\/story\.php\?story_fbid=([0-9]+)&id=([0-9]+)/', $html, $matches)) {
    sendTelegram($telegramBotToken, $telegramChatId, "⚠️ لم يتم العثور على منشور");
    exit;
}

$postUrl = "https://www.facebook.com/story.php?story_fbid={$matches[1]}&id={$matches[2]}";

/********************
 * جلب صفحة المنشور نفسه
 ********************/
$postHtml = fetchPage("https://mbasic.facebook.com" . $matches[0]);

$text = "";
if (preg_match('/<div[^>]*>(.*?)<\/div>/s', $postHtml, $textMatch)) {
    $text = trim(strip_tags(html_entity_decode($textMatch[1])));
}

/********************
 * منع التكرار
 ********************/
$currentHash = sha1($postUrl . $text);
$lastHash = getLastHash($hashFile);

if ($currentHash === $lastHash) {
    // لا يوجد جديد
    exit;
}

saveHash($hashFile, $currentHash);

/********************
 * إرسال إشعار تلجرام
 ********************/
$message  = "🆕 منشور جديد من صفحة العربية\n\n";
if ($text) {
    $message .= "📝 النص:\n" . mb_substr($text, 0, 1500) . "\n\n";
}
$message .= "🔗 الرابط:\n" . $postUrl;

sendTelegram($telegramBotToken, $telegramChatId, $message);
