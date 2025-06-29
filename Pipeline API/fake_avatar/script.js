document.addEventListener("DOMContentLoaded", () => {
  const initialPromptValues = {
    skin_colour: "{skin_colour}",
    age: "{age}",
    gender: "{gender}",
    primary_action: "{primary action}",
    context: "{context}",
    expression: "{expression}",
    hair_colour: "{hair colour}",
    hair_length: "{hair length}",
    hair_style: "{hair style}",
    eye_colour: "{eye colour}",
    imperfections: "{imperfections}",
    clothing: "{clothing}"
  };

  // Update prompt spans when dropdown changes
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

function buildWeightedPrompt() {
  const promptBox = document.querySelector(".prompt-box");
  const nodes = Array.from(promptBox.childNodes);

  const combinedKeys = ["age", "skin_colour", "gender"];
  const getValue = (key) => {
    return document.getElementById(key)?.value.trim() || initialPromptValues[key] || `{${key}}`;
  };

  let combinedPhraseParts = [];
  let combinedStarted = false;
  let combinedEnded = false;

  let restParts = [];

  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];

    if (!combinedEnded) {
      if (
        (node.nodeType === Node.ELEMENT_NODE && combinedKeys.includes(node.dataset.placeholder)) ||
        (node.nodeType === Node.TEXT_NODE && combinedStarted)
      ) {
        combinedStarted = true;

        if (node.nodeType === Node.ELEMENT_NODE) {
          combinedPhraseParts.push(getValue(node.dataset.placeholder));
        } else if (node.nodeType === Node.TEXT_NODE) {
          combinedPhraseParts.push(node.textContent);
        }

        if (
          node.nodeType === Node.ELEMENT_NODE &&
          node.dataset.placeholder === combinedKeys[combinedKeys.length - 1]
        ) {
          combinedEnded = true;
        }
        continue;
      }
    }

    if (combinedEnded) {
      // Only after combined block ended, add nodes to restParts
      if (node.nodeType === Node.TEXT_NODE) {
        restParts.push(node.textContent);
      } else if (node.nodeType === Node.ELEMENT_NODE && node.dataset.placeholder) {
        restParts.push(getValue(node.dataset.placeholder));
      }
    } else {
      // Before combined block started, add normally
      if (node.nodeType === Node.TEXT_NODE) {
        restParts.push(node.textContent);
      } else if (node.nodeType === Node.ELEMENT_NODE && node.dataset.placeholder) {
        restParts.push(getValue(node.dataset.placeholder));
      }
    }
  }

  const combinedPhrase = combinedPhraseParts.join('').replace(/\s+/g, ' ').trim();
  const weightedCombined = `A (${combinedPhrase}::1.5)`;

  let promptText = restParts.join('').replace(/\s*\n\s*/g, ' ').replace(/\s{2,}/g, ' ').trim();

  // Weight the background
  const bgMatch = promptText.match(/The background is .*?with little details\./i);
  if (bgMatch) {
    const bgText = bgMatch[0];
    promptText = promptText.replace(bgText, `(${bgText}::1.2)`);
  }

  const nuance = `((KidV2 captures natural shadows::1.3) while (maintaining playful energy::1.4))`;

  return `${weightedCombined} ${promptText} ${nuance}.`;
}





  // Generate button click
  const generateBtn = document.querySelector('.generate-btn:not(.reset-btn)');
  if (generateBtn) {
    generateBtn.addEventListener('click', () => {
      console.log("Generate button clicked");

      const batchSize = document.getElementById("batch_size").value || "1";
      console.log("Batch size:", batchSize);

      const promptText = buildWeightedPrompt();
      console.log("Prompt to send:", promptText);

      alert("Successfully started generating!");

      fetch('http://127.0.0.1:8189/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
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
        const avatars = data.images || [];
        const avatarGrid = document.querySelector('.avatar-grid');
        if (avatarGrid) {
          avatarGrid.innerHTML = '';
          avatars.forEach(url => {
            const wrapper = document.createElement('div');
            wrapper.classList.add('avatar-placeholder');

            const img = document.createElement('img');
            img.src = `http://127.0.0.1:8189${url}`;
            img.alt = "Generated Avatar";
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '10px';

            wrapper.appendChild(img);
            avatarGrid.appendChild(wrapper);
          });
        }
      })
      .catch(error => {
        console.error("Error generating avatar:", error);
        alert("There was a problem generating the avatar.");
      });
    });
  }

  // Reset button click
  const resetBtn = document.querySelector('.reset-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      console.log("Reset button clicked");

      document.querySelectorAll('.form-grid select').forEach(select => {
        select.value = ""; // Reset all selects to default empty option
        const key = select.getAttribute('data-key');
        const span = document.querySelector(`.prompt-box [data-placeholder="${key}"]`);
        if (span) {
          span.textContent = initialPromptValues[key];
        }
      });
    });
  }

  // Modal and Save logic remain unchanged
  // ...

  // Modal Logic
  const modal = document.getElementById('avatar-modal');
  const modalAvatar = modal.querySelector('.modal-avatar');
  const selectBtn = document.getElementById('select-avatar-btn');
  const closeBtn = document.getElementById('close-modal-btn');

  let currentPlaceholder = null;

  document.querySelector('.avatar-grid').addEventListener('click', (e) => {
    const placeholder = e.target.closest('.avatar-placeholder');
    if (!placeholder) return;

    currentPlaceholder = placeholder;
    const img = placeholder.querySelector('img');

    if (img) {
      modalAvatar.style.backgroundImage = `url(${img.src})`;
    } else {
      modalAvatar.style.backgroundImage = 'none';
    }

    modal.classList.remove('hidden');
  });

  selectBtn.addEventListener('click', () => {
    if (!currentPlaceholder) return;

    document.querySelectorAll('.avatar-placeholder.selected').forEach(ph => ph.classList.remove('selected'));
    currentPlaceholder.classList.add('selected');
    modal.classList.add('hidden');
  });

  closeBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  modal.addEventListener('click', e => {
    if (e.target === modal) {
      modal.classList.add('hidden');
    }
  });

  // Save Avatar
  const saveBtn = document.querySelector(".save-btn");
  const nameInput = document.querySelector(".avatar-preview input");

  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const selected = document.querySelector(".avatar-placeholder.selected img");
      const avatarName = nameInput.value.trim();

      if (!selected) {
        alert("Please select an avatar image.");
        return;
      }

      if (!avatarName) {
        alert("Please enter a name for the avatar.");
        return;
      }

      const selectedImageSrc = selected.src;

      fetch('http://127.0.0.1:8189/saveImage', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          name: avatarName,
          img: selectedImageSrc
        })
      })
      .then(res => {
        if (!res.ok) throw new Error("Failed to save avatar.");
        return res.json();
      })
      .then(response => {
        alert("Avatar saved successfully!");
        nameInput.value = "";
        document.querySelectorAll('.avatar-placeholder').forEach(ph => ph.classList.remove('selected'));
      })
      .catch(err => {
        console.error("Error saving avatar:", err);
        alert("There was a problem saving the avatar.");
      });
    });
  }
});
