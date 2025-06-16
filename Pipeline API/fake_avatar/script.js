console.log("✅ script.js is loaded");

const initialPromptValues = {
  skin_colour: "{skin_colour}",
  age: "{age}",
  gender: "{gender}",
  primary_action: "{primary_action}",
  context_activity: "{context_activity}",
  expression: "{expression}"
};

document.addEventListener("DOMContentLoaded", () => {
  // Update prompt spans when a dropdown changes
  document.querySelectorAll('.form-grid select').forEach(select => {
    select.addEventListener('change', function () {
      const key = this.getAttribute('data-key');
      const value = this.value || initialPromptValues[key];
      const span = document.querySelector(`.prompt-box [data-placeholder="${key}"]`);
      if (span) {
        span.textContent = value;
      }
    });
  });

  
  const generateBtn = document.querySelector('.generate-btn');
  if (generateBtn) {
    generateBtn.addEventListener('click', () => {
      // Handle the generate button click
      console.log("✅ Generate button was clicked");

      const batchSize = document.getElementById("batch_size").value; // default to 1
      console.log("Batch size:", batchSize);


      const promptBox = document.querySelector('.prompt-box');
      if (!promptBox) return;

      // Get the current prompt string (including manual edits)
      const promptText = promptBox.textContent.trim();

      // Debug: log the prompt
      console.log("Sending prompt:", promptText, batchSize);

      // Send it to the API
      // fetch('http://127.0.0.1:8189/generate', { 
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({ prompt: promptText })
      // })

      fetch('http://127.0.0.1:8189/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: promptText,
          batch_size: batchSize
        })
      })

      .then(response => {
        if (!response.ok) throw new Error("Failed to generate avatar");
        return response.json();
      })
      .then(data => {
        // Assume the API returns an array of image URLs: { images: [url1, url2, ...] }
        const avatars = data.images || [];

        const avatarGrid = document.querySelector('.avatar-grid');
        if (avatarGrid) {
          avatarGrid.innerHTML = ''; // Clear any placeholders or previous results
          avatars.forEach(url => {
            const img = document.createElement('img');
            img.src = `http://127.0.0.1:8189${url}`; // Adjust the URL as needed
            img.classList.add('avatar-image'); // Optional for styling
            avatarGrid.appendChild(img);
          });
        }
      })
      .catch(error => {
        console.error("Error generating avatar:", error);
        alert("There was a problem generating the avatar.");
      });
    });
  }

  // Reset button logic
  const resetBtn = document.querySelector('.reset-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      // Reset all selects
      console.log("✅ reset button was clicked");

      document.querySelectorAll('.form-grid select').forEach(select => {
        select.selectedIndex = 0;
      });


      // Reset prompt to default
      const promptBox = document.querySelector('.prompt-box');
      if (promptBox) {
        promptBox.innerHTML =
          `A <span data-placeholder="skin_colour">{skin_colour}</span> ` +
          `<span data-placeholder="age">{age}</span>-year-old ` +
          `<span data-placeholder="gender">{gender}</span> ` +
          `<span data-placeholder="primary_action">{primary_action}</span> while ` +
          `<span data-placeholder="context_activity">{context_activity}</span>, with a ` +
          `<span data-placeholder="expression">{expression}</span> expression.`;
      }
    });
  }
});

