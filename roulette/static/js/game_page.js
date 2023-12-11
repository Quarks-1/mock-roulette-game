"use strict"

let selectedChip = 1; // Default chip value
let totalBet = 0; // Total bet amount
let currentBet = {}; // {number: amount}

function selectChip(value) {
    // Remove 'selected' class from all chips
    let chips = document.getElementsByClassName("chip");
    for (let i = 0; i < chips.length; i++) {
        chips[i].classList.remove("selected");
    }

    selectedChip = value;

    // Add 'selected' class to the selected chip
    document.getElementById("chip_" + value).classList.add("selected");

    let roll = document.getElementById("roll");
    if (roll.innerHTML.startsWith("Winning")) {
        document.getElementById("status").innerHTML = 'Waiting for all players to make bets...';
        roll.innerHTML = "";
    }

}

/**
 * @brief: Add to current bet
 */
function addToBet(button) {
    if (selectedChip == 0) {
        return;
    }

    let value = button.parentElement.getAttribute('data-value');

    totalBet += selectedChip;
    if (currentBet.hasOwnProperty(value)) {
        currentBet[value] += selectedChip;
    }
    else {
        currentBet[value] = selectedChip;
    }
    document.getElementById("total_bet").innerHTML = totalBet;

}

/**
 * @brief: Reset current bet selection
 */
function clearBet() {
    totalBet = 0;
    currentBet = {};
    selectedChip = 0;
    document.getElementById("total_bet").innerHTML = 0;

    let chips = document.getElementsByClassName("chip");
    for (let i = 0; i < chips.length; i++) {
        chips[i].classList.remove("selected");
    }
}

/**
 * @brief: Place the bet for this round
 */
function placeBet() {
    if (totalBet <= 0) {
        return;
    }

    let data = { "action": "place_bet", "bets": currentBet, 'totalBet': totalBet }
    socket.send(JSON.stringify(data))

    let chipsAudio = document.getElementById("sound");
    chipsAudio.src = "https://dm0qx8t0i9gc9.cloudfront.net/previews/audio/BsTwCwBHBjzwub4i4/shuffling-poker-chips_NWM.mp3";
    chipsAudio.load();
    chipsAudio.play();
}


function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}

let socket = null

function connectToServer() {
    // Use wss: protocol if site using https:, otherwise use ws: protocol
    let wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"

    // Create a new WebSocket.
    let url = `${wsProtocol}//${window.location.host}/roulette/data`
    socket = new WebSocket(url)

    // Handle any errors that occur.
    socket.onerror = function (error) {
        console.log("WebSocket Error: " + error)
    }

    // Show a connected message when the WebSocket is opened.
    socket.onopen = function (event) {
        console.log("WebSocket Connected")
    }

    // Show a disconnected message when the WebSocket is closed.
    socket.onclose = function (event) {
        console.log("WebSocket Disconnected")
    }

    // Handle messages received from the server.
    socket.onmessage = function (event) {
        console.log("WebSocket Message Received")
        let data = JSON.parse(event.data)
        // Update user balance on game page
        if (data['type'] === 'balance') {
            document.getElementById("player_balance").innerHTML = data['balance'];
            document.getElementById("total_bet").innerHTML = data['totalBet'];
            if (data['showWin'] === true) {
                if (data['winnings'] > 0) {
                    setTimeout(() => {
                        let spinwheel = document.getElementById("spinwheel");
                        spinwheel.style.display = "none";

                        document.getElementById("status").innerHTML = 'You won: $' + data['winnings'] + '!';

                        let winnerAudio = document.getElementById("sound");
                        winnerAudio.src = "https://dm0qx8t0i9gc9.cloudfront.net/previews/audio/BsTwCwBHBjzwub4i4/jackpot_NWM.mp3";
                        winnerAudio.load();
                        winnerAudio.currentTime = 47;
                        winnerAudio.play();
                    }, 5000);
                }
                else if (data['winnings'] < 0) {
                    setTimeout(() => {
                        let spinwheel = document.getElementById("spinwheel");
                        spinwheel.style.display = "none";

                        document.getElementById("status").innerHTML = 'You lost: $' + (data['winnings'] * -1) + '!';

                        let loserAudio = document.getElementById("sound");
                        loserAudio.src = "https://dm0qx8t0i9gc9.cloudfront.net/previews/audio/BsTwCwBHBjzwub4i4/audioblocks-fail-error-mistake-out-of-time-sound-error-mistake-out-of-time-sound_SYoWmAb8CwI_NWM.mp3";
                        loserAudio.load();
                        loserAudio.play();
                    }, 5000);

                }
                else if (data['totalBet'] === 0) {
                    document.getElementById("status").innerHTML = "You didn't bet anything!";
                }
                else {
                    document.getElementById("status").innerHTML = 'You broke even!';
                }
            }
            else {
                document.getElementById("status").innerHTML = 'Waiting for all players to make bets...';
            }
            clearBet(); // Clear bet after each round


        }
        // Update currently joined user list
        if (data['type'] === 'joined_list') {
            const profiles = data['joined'];
            let user_list = document.getElementById("user_names");
            let user_pictures = document.getElementById("user_pictures");
            // Clear the user list
            user_list.innerHTML = '';
            user_pictures.innerHTML = '';
            // Add each user to the user list
            for (let i = 0; i < profiles.length; i++) {
                let profile = profiles[i];
                let pic_td = document.createElement('td');
                let img = document.createElement('img');
                img.src = profile['picture'];
                pic_td.appendChild(img);
                user_pictures.appendChild(pic_td);
                // Add name
                let name_td = document.createElement('td');
                name_td.textContent = profile['fname'];
                // Set color based on ready status
                if (profile['ready'] === true) {
                    name_td.setAttribute('bgcolor', 'green');
                }
                else {
                    name_td.setAttribute('bgcolor', 'red');
                }
                user_list.appendChild(name_td);
            }
        }

        if (data['type'] == 'spin') {
            let spinwheel = document.getElementById("spinwheel");
            spinwheel.style.display = "block";
        }

        // Update board values which have bets
        if (data['type'] === 'bet_list') {
            // clear all values
            let numbers = Array.from({ length: 37 }, (_, i) => i);
            let other = ['1st 12', '2nd 12', '3rd 12', '1 to 18', '19 to 36', 'Even', 'Odd', 'Red', 'Black', '2 to 1 (1)', '2 to 1 (2)', '2 to 1 (3)'];
            let all = numbers.concat(other);
            for (let i = 0; i < all.length; i++) {
                let bet_t = document.getElementById(all[i]);
                // Skip if bet_t is null
                if (bet_t === null) {
                    continue;
                }
                bet_t.innerHTML = 'Current bets:';
            }
            // add new values
            const bets = data['bets'];
            for (let j = 0; j < bets.length; j++) {
                let bet = bets[j];
                let bet_value = bet['value'];
                let bet_amount = bet['amount'];
                let bet_name = bet['name'];
                let bet_t = document.getElementById(bet_value);
                let bet_text = document.createElement('tr');
                bet_text.textContent = bet_name + ": " + bet_amount;
                bet_t.appendChild(bet_text);
            }
        }
        // Update winning number
        if (data['type'] === 'winning_number') {
            setTimeout(() => {
                let spinwheel = document.getElementById("spinwheel");
                spinwheel.style.display = "none";

                let winning_number = data['winning_number'];
                let status = document.getElementById("roll");
                status.innerHTML = 'Winning number: ' + winning_number;
                window.scrollTo({ top: status.offsetTop, behavior: 'smooth' });
            }, 5000);
        }

        if (data['type'] === 'error') {
            let status = document.getElementById("status");
            status.innerHTML = data['error'];
        }
    }
}

function openInstructionModal() {
    let modal = document.getElementById("instructions-modal");
    modal.style.display = "block";
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "hidden";
        }
    }
}

function closeModal(event) {
    let modal = document.getElementById("instructions-modal");
    modal.style.display = "none";
}

// Code to handle dropdown menus
document.onmousemove = function (e) {
    let dropdowns = document.querySelectorAll('.dropdown-content-board');
    dropdowns.forEach(function (dropdown) {
        let offsetX = 5; // Offset from the cursor, adjust as needed
        let offsetY = 70; // Offset from the cursor, adjust as needed

        let left = e.pageX + offsetX;
        let top = e.pageY - offsetY;

        // Ensure the dropdown doesn't go beyond the viewport
        left = Math.min(left, window.innerWidth - dropdown.offsetWidth);
        top = Math.min(top, window.innerHeight - dropdown.offsetHeight);

        dropdown.style.left = left + 'px';
        dropdown.style.top = top + 'px';
    });
};

window.onload = function () {
    document.getElementById("background-music").play();
}