/**
 * Firebase Konfigurasyonu
 * =======================
 * ADIMLAR:
 * 1. https://console.firebase.google.com adresine git
 * 2. Projenize tiklayip Project Settings'e gidin
 * 3. "Your apps" bolumunden Web uygulamanizi secin (yoksa "Add app" > Web ile olusturun)
 * 4. firebaseConfig degerlerini asagidaki placeholder'larin yerine yapistin
 * 5. Firebase Console > Firestore Database > Create database > Start in test mode
 * 6. Kurallari su sekilde guncelleyin:
 *    rules_version = '2';
 *    service cloud.firestore {
 *      match /databases/{database}/documents {
 *        match /enkaz_bildirimleri/{document=**} {
 *          allow read, write: if true;
 *        }
 *      }
 *    }
 */

const firebaseConfig = {
  apiKey: "AIzaSyCCcoFpkb7wLpzOef0W-5ov1HBNbUw5OBQ",
  authDomain: "afet-rota-sistemi.firebaseapp.com",
  projectId: "afet-rota-sistemi",
  storageBucket: "afet-rota-sistemi.firebasestorage.app",
  messagingSenderId: "904633185691",
  appId: "1:904633185691:web:f57796225cd16fbdbb5d3e"
};

// Firebase baslatma — SDK HTML'de yuklendikten sonra calisir
let db = null;

function initFirebase() {
    try {
        if (typeof firebase !== 'undefined' && firebaseConfig.apiKey !== "BURAYA_API_KEY") {
            firebase.initializeApp(firebaseConfig);
            db = firebase.firestore();
            console.log("Firebase Firestore baglantisi basarili.");
            return true;
        } else if (firebaseConfig.apiKey === "BURAYA_API_KEY") {
            console.warn("Firebase yapilandirilmamis. firebase-config.js dosyasindaki degerleri doldurun.");
            return false;
        }
    } catch (e) {
        console.error("Firebase baglanti hatasi:", e);
        return false;
    }
    return false;
}
