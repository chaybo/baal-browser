![alt text](https://github.com/chaybo/baal-browser/blob/main/images/browser.png?raw=true)

<h1><strong>Asset Store</strong></h1>

<p>Asset store for saving and versioning up asset files,</p>

<p>- Can be used for multiple shows/projects via drop down menu<br />
- Add notes per publish<br />
- Checks for dirty scenes, namespaces etc before publish<br />
- Swap between .mb or .ma<br />
- Import files into current scene<br />
- Generates out a single line of code to import the asset for use elsewhere or in other code<br />
- Can navigate and browse maya files in other defined folders separate to the asset store itself</p>

<h2>Installing</h2>

<ol dir="auto">
	<li>
	<p>Modify settings.json by replacing the following with your folder paths, you can use the provided sample folders to test, or make your own</p>
	</li>
</ol>

<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &quot;asset_directory&quot;: &quot;E:\\git\\asset_store&quot;,<br />
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &quot;current_directory&quot;: &quot;E:\\git\\Current&quot;,<br />
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &quot;archive_directory&quot;: &quot;E:\\git\\Archives&quot;,<br />
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &quot;window_icon&quot;: &quot;E:/git/baalIcon.ico&quot;</p>

<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2. Run the following in maya, replacing the location of your script into this</p>

<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; import sys; import importlib; sys.path.append(&#39;E:/git&#39;);<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; from asset_store import show_ui; importlib.reload(sys.modules[&#39;asset_store&#39;]); show_ui()</p>

<p>&nbsp;</p>
