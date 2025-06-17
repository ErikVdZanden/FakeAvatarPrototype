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
      console.log("✅ Generate button was clicked");

      const batchSize = document.getElementById("batch_size").value;
      console.log("Batch size:", batchSize);

      const promptBox = document.querySelector('.prompt-box');
      if (!promptBox) return;

      const promptText = promptBox.textContent.trim();
      console.log("Sending prompt:", promptText, batchSize);

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

  const resetBtn = document.querySelector('.reset-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      console.log("✅ reset button was clicked");

      document.querySelectorAll('.form-grid select').forEach(select => {
        select.selectedIndex = 0;
      });

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

  // ----------- Save Avatar Logic -----------

  const saveBtn = document.querySelector(".save-btn");
  const nameInput = document.querySelector(".avatar-name-input");

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
      const existingAvatars = JSON.parse(localStorage.getItem("avatars")) || [];

      existingAvatars.push({
        name: avatarName,
        img: selectedImageSrc
      });

      localStorage.setItem("avatars", JSON.stringify(existingAvatars));

      alert("✅ Avatar saved successfully!");
      nameInput.value = "";
      document.querySelectorAll('.avatar-placeholder').forEach(ph => ph.classList.remove('selected'));
    });
  }

  // ----------- Load Avatars on View Page -----------

  const avatarsGrid = document.querySelector(".avatars-grid");
  if (avatarsGrid) {
    const savedAvatars = JSON.parse(localStorage.getItem("avatars")) || [];
    avatarsGrid.innerHTML = "";

    if (savedAvatars.length === 0) {
      avatarsGrid.innerHTML = "<p>No avatars saved yet.</p>";
    } else {
      savedAvatars.forEach(({ name, img }) => {
        const card = document.createElement("div");
        card.classList.add("avatar-card");

        const image = document.createElement("img");
        image.src = img;
        image.alt = name;

        const label = document.createElement("p");
        label.textContent = name;

        card.appendChild(image);
        card.appendChild(label);

        avatarsGrid.appendChild(card);
      });
    }
  }
});